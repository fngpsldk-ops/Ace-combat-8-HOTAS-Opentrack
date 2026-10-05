"""AC8 HOTAS 브리지: 스틱/스로틀(+OpenTrack) → 가상 Xbox 360 패드.

Ctrl+C로 종료하면 가상 패드를 중립으로 돌리고 정리한다.
"""
import ctypes
import math
import os
import socket
import struct
import time

import vgamepad as vg

from ac8_i18n import T
from ac8_common import (CONFIG_PATH, VERSION, clamp, find_device, init_pygame, load_config, open_all,
                        pygame, rescaled_deadzone, shape_axis, signed_power, split_throttle)

B = vg.XUSB_BUTTON
SIMPLE_BUTTONS = {
    "gun": B.XUSB_GAMEPAD_A,
    "missile": B.XUSB_GAMEPAD_B,
    "weapon": B.XUSB_GAMEPAD_X,
    "target": B.XUSB_GAMEPAD_Y,
    "boresight": B.XUSB_GAMEPAD_LEFT_THUMB,
    "camera": B.XUSB_GAMEPAD_RIGHT_THUMB,
    "map": B.XUSB_GAMEPAD_BACK,
    "pause": B.XUSB_GAMEPAD_START,
}
ALL_BUTTONS = list(SIMPLE_BUTTONS.values()) + [
    B.XUSB_GAMEPAD_LEFT_SHOULDER, B.XUSB_GAMEPAD_RIGHT_SHOULDER,
    B.XUSB_GAMEPAD_DPAD_UP, B.XUSB_GAMEPAD_DPAD_DOWN,
    B.XUSB_GAMEPAD_DPAD_LEFT, B.XUSB_GAMEPAD_DPAD_RIGHT,
]


def angle_to_stick(deg, deadzone, full_scale, exponent, anti_deadzone=0.0):
    """머리 각도 → 스틱(-1~1). 데드존 안은 0, 데드존~최대각을 0~1로 늘린 뒤 커브 적용.
    anti_deadzone: 0이 아닌 출력을 이 값부터 시작시켜 게임 쪽 스틱 데드존을 건너뛴다."""
    a = abs(deg)
    if a <= deadzone or full_scale <= deadzone:
        return 0.0
    n = min(1.0, (a - deadzone) / (full_scale - deadzone))
    n = abs(signed_power(n, exponent))
    n = anti_deadzone + (1.0 - anti_deadzone) * n
    return n if deg > 0 else -n


class FTData(ctypes.Structure):
    """FreeTrack 공유 메모리(FT_SharedMem) 앞부분. 회전은 라디안, OpenTrack이 yaw/pitch 부호를 뒤집어 씀."""
    _fields_ = [("DataID", ctypes.c_uint32), ("CamWidth", ctypes.c_int32), ("CamHeight", ctypes.c_int32),
                ("Yaw", ctypes.c_float), ("Pitch", ctypes.c_float), ("Roll", ctypes.c_float),
                ("X", ctypes.c_float), ("Y", ctypes.c_float), ("Z", ctypes.c_float)]


class FreeTrackReader:
    """OpenTrack 'freetrack 2.0 Enhanced' 출력을 공유 메모리에서 읽는다(항상 최신 값 하나)."""
    FILE_MAP_READ = 0x0004

    def __init__(self):
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.open_map = k32.OpenFileMappingW
        self.open_map.restype = ctypes.c_void_p
        self.open_map.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
        self.map_view = k32.MapViewOfFile
        self.map_view.restype = ctypes.c_void_p
        self.map_view.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
        self.data = None
        self.next_try = 0.0
        self.last_id = None

    def read(self):
        """새 값이 있으면 (yaw_deg, pitch_deg), 없으면 None."""
        if self.data is None:
            now = time.perf_counter()
            if now < self.next_try:
                return None
            self.next_try = now + 1.0
            h = self.open_map(self.FILE_MAP_READ, False, "FT_SharedMem")
            if not h:
                return None
            p = self.map_view(h, self.FILE_MAP_READ, 0, 0, ctypes.sizeof(FTData))
            if not p:
                return None
            self.data = FTData.from_address(p)
        d = self.data
        if d.DataID == self.last_id:
            return None
        self.last_id = d.DataID
        return -math.degrees(d.Yaw), -math.degrees(d.Pitch)


class UdpReader:
    """OpenTrack 'UDP over network' 출력 수신: double 6개(x,y,z,yaw,pitch,roll). 마지막 값만 사용."""

    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", int(port)))
        self.sock.setblocking(False)

    def read(self):
        latest = None
        while True:
            try:
                data = self.sock.recv(1024)
            except (BlockingIOError, ConnectionResetError):
                break
            if len(data) >= 48:
                v = struct.unpack("<6d", data[:48])
                latest = (v[3], v[4])
        return latest


class HeadTracker:
    def __init__(self, ht):
        self.ht = ht
        if ht["source"] == "udp":
            self.reader = UdpReader(ht["udp_port"])
        else:
            self.reader = FreeTrackReader()
        self.yaw = self.pitch = 0.0
        self.vyaw = self.vpitch = 0.0
        self.last = 0.0
        self.sx = self.sy = 0.0
        # 진단용: 초당 수신 패킷 수, 끊김(stale 진입) 횟수
        self.count = 0
        self.rate = 0
        self.rate_t = time.perf_counter()
        self.drops = 0
        self.was_fresh = False

    def poll(self):
        v = self.reader.read()
        now = time.perf_counter()
        if v:
            # 머리 회전 속도(°/s) 추정: 새 샘플 사이 변화량, 잡음은 짧게 평균
            gap = now - self.last
            if 0.0 < gap < 0.1:
                k = 1.0 - math.exp(-gap / 0.04)
                self.vyaw += k * ((v[0] - self.yaw) / gap - self.vyaw)
                self.vpitch += k * ((v[1] - self.pitch) / gap - self.vpitch)
            else:
                self.vyaw = self.vpitch = 0.0
            self.yaw, self.pitch = v
            self.last = now
            self.count += 1
        if now - self.rate_t >= 1.0:
            self.rate, self.count, self.rate_t = self.count, 0, now
        fresh = self.fresh()
        if self.was_fresh and not fresh:
            self.drops += 1
        self.was_fresh = fresh

    def status(self, on):
        if not self.fresh():
            return f"{T('st_head_none')}({T('st_drops')}{self.drops})"
        return (f"HEAD-{'ON' if on else 'OFF'} {T('st_angle')}{self.yaw:+.0f}°/{self.pitch:+.0f}° "
                f"{T('st_rx')}{self.rate}Hz {T('st_drops')}{self.drops}")

    def fresh(self):
        return time.perf_counter() - self.last < self.ht["stale_timeout_sec"]

    def stick(self, dt):
        ht = self.ht
        if self.fresh():
            dz, adz, lead = ht["deadzone_deg"], ht["anti_deadzone"], ht["lead_sec"]
            # 선행 입력: 돌리는 중엔 회전 속도 × lead_sec 만큼 앞선 각도를 보낸다
            # (가만히 있을 때의 떨림은 lead_min_speed 아래라 무시)
            vmin = ht["lead_min_speed"]

            def over(v):
                return math.copysign(abs(v) - vmin, v) if abs(v) > vmin else 0.0
            yaw = self.yaw + lead * over(self.vyaw)
            pitch = self.pitch + lead * over(self.vpitch)
            # 원형 처리: 방향은 유지하고 데드존·안티데드존·커브는 크기에만 적용(대각선 왜곡 방지).
            # 상하는 좌우 각도 단위로 환산해 한 원 위에서 계산한다.
            yfs, pfs = ht["yaw_full_scale_deg"], ht["pitch_full_scale_deg"]
            p_as_yaw = pitch * yfs / pfs
            r = math.hypot(yaw, p_as_yaw)
            m = angle_to_stick(r, dz, yfs, ht["yaw_exponent"], adz)
            x = m * yaw / r if r > 0 else 0.0
            y = m * p_as_yaw / r if r > 0 else 0.0
            if ht["invert_x"]:
                x = -x
            if ht["invert_y"]:
                y = -y
        else:
            x = y = 0.0
        tau = ht["smoothing_sec"]
        k = 1.0 if tau <= 0 else 1.0 - math.exp(-dt / tau)
        self.sx += k * (x - self.sx)
        self.sy += k * (y - self.sy)
        return self.sx, self.sy

    def reset(self):
        self.sx = self.sy = 0.0


class Bridge:
    def __init__(self, cfg):
        self.cfg = cfg
        self.s = cfg["settings"]
        self.cal = dict(cfg["throttle_cal"], half_width=self.s["throttle_neutral_half_width"])
        self.pad = vg.VX360Gamepad()
        self.devs = {}
        self.head = HeadTracker(cfg["headtrack"]) if cfg["headtrack"]["enabled"] else None
        self.head_on = True
        self.toggle_prev = False
        self.cfg_mtime = os.path.getmtime(CONFIG_PATH)
        self.connect()

    # ---------- 장비 ----------
    def needed_aliases(self):
        a = self.cfg["axes"]
        used = {a["roll"]["dev"], a["pitch"]["dev"]} | {lv["dev"] for lv in a.get("throttle", []) if lv}
        return used

    def connect(self):
        pygame.event.pump()
        found = open_all()
        self.devs = {alias: find_device(found, info) for alias, info in self.cfg["devices"].items()}
        missing = [self.cfg["devices"][a]["name"] for a in self.needed_aliases() if not self.devs.get(a)]
        for alias, d in self.devs.items():
            print(f"  {alias:9s}: {d.get_name() if d else T('br_not_connected')}")
        # 서로 다른 설정 장비가 같은 실제 장비로 잡히면 입력이 섞인다
        seen = {}
        for alias, d in self.devs.items():
            if d:
                other = seen.setdefault(d.get_instance_id(), alias)
                if other != alias:
                    print(T("br_same_device", a=other, b=alias, name=d.get_name()))
        if missing and not any("xbox 360" not in d.get_name().lower() for d in found):
            print(T("no_devices"))
        return not missing

    def axis(self, entry):
        if not entry:
            return 0.0
        d = self.devs.get(entry["dev"])
        if not d:
            return 0.0
        v = d.get_axis(entry["axis"])
        return -v if entry["invert"] else v

    def button(self, action):
        b = self.cfg["buttons"].get(action)
        d = self.devs.get(b["dev"]) if b else None
        return bool(d and d.get_button(b["button"]))

    # ---------- 출력 ----------
    def neutral(self):
        self.pad.reset()
        self.pad.update()
        if self.head:
            self.head.reset()

    def step(self, dt):
        a, s = self.cfg["axes"], self.s
        g, e, adz = s["stick_gain"], s["stick_exponent"], s["stick_anti_deadzone"]
        roll = shape_axis(self.axis(a["roll"]), s["roll_deadzone"], g, e, adz)
        pitch = shape_axis(self.axis(a["pitch"]), s["pitch_deadzone"], g, e, adz)
        yaw = self.axis(a.get("yaw"))
        levers = [self.axis(lv) for lv in a.get("throttle", []) if lv]
        lt, rt = split_throttle(sum(levers) / len(levers), self.cal) if levers else (0.0, 0.0)
        # 스로틀 대신(또는 함께) 쓰는 가속/감속 버튼
        if self.button("throttle_up"):
            rt = 1.0
        if self.button("throttle_down"):
            lt = 1.0

        pressed = {k for k in SIMPLE_BUTTONS if self.button(k)}
        lb = yaw < -s["yaw_threshold"]
        rb = yaw > s["yaw_threshold"]
        if self.button("autopilot"):
            lb = rb = True
        if self.button("flare"):
            pressed |= {"boresight", "camera"}
        if self.button("highg"):
            lt = rt = 1.0

        # 헤드트래킹 토글
        t = self.button("head_toggle")
        if t and not self.toggle_prev:
            self.head_on = not self.head_on
            print("\n" + T("br_head_on" if self.head_on else "br_head_off"))
        self.toggle_prev = t

        # 오른쪽 스틱 = 헤드트래킹 + 슬루 스틱
        cx = cy = 0.0
        if self.head:
            self.head.poll()
            hx, hy = self.head.stick(dt)
            if self.head_on:
                cx, cy = hx, hy
        sx = rescaled_deadzone(self.axis(a.get("slew_x")), s["slew_deadzone"])
        sy = rescaled_deadzone(self.axis(a.get("slew_y")), s["slew_deadzone"])
        cx, cy = clamp(cx + sx), clamp(cy + sy)

        # D-패드 ← POV 햇
        hat = self.cfg.get("hat")
        hx = hy = 0
        if hat and self.devs.get(hat["dev"]):
            hx, hy = self.devs[hat["dev"]].get_hat(hat["hat"])

        want = {SIMPLE_BUTTONS[k] for k in pressed}
        if lb:
            want.add(B.XUSB_GAMEPAD_LEFT_SHOULDER)
        if rb:
            want.add(B.XUSB_GAMEPAD_RIGHT_SHOULDER)
        if hy > 0:
            want.add(B.XUSB_GAMEPAD_DPAD_UP)
        if hy < 0:
            want.add(B.XUSB_GAMEPAD_DPAD_DOWN)
        if hx < 0:
            want.add(B.XUSB_GAMEPAD_DPAD_LEFT)
        if hx > 0:
            want.add(B.XUSB_GAMEPAD_DPAD_RIGHT)
        for btn in ALL_BUTTONS:
            if btn in want:
                self.pad.press_button(button=btn)
            else:
                self.pad.release_button(button=btn)

        self.pad.left_joystick_float(x_value_float=roll, y_value_float=pitch)
        self.pad.right_joystick_float(x_value_float=cx, y_value_float=cy)
        self.pad.left_trigger_float(value_float=lt)
        self.pad.right_trigger_float(value_float=rt)
        self.pad.update()

        return (f"R{roll:+.2f} P{pitch:+.2f} Y{yaw:+.2f}{'[LB]' if lb else ''}{'[RB]' if rb else ''} "
                f"LT{lt:.2f} RT{rt:.2f} CAM{cx:+.2f},{cy:+.2f} "
                f"{self.head.status(self.head_on) if self.head else ''}")

    def reload_if_changed(self):
        """config.json이 바뀌면 전부 다시 읽는다(헤드트래킹 켜기/끄기·입력 방식만 재시작 필요).
        바뀌지 않았으면 None, 바뀌었으면 필요한 장비가 모두 연결됐는지(bool)."""
        try:
            mtime = os.path.getmtime(CONFIG_PATH)
            if mtime == self.cfg_mtime:
                return None
            self.cfg_mtime = mtime
            cfg = load_config()
        except (OSError, ValueError) as e:  # 저장 도중이면 다음에 다시
            print("\n" + T("br_reload_fail", e=e))
            self.cfg_mtime = None
            return None
        if self.head:
            src = self.head.ht["source"]
            self.head.ht.update(cfg["headtrack"], source=src)
            cfg["headtrack"] = self.head.ht
        self.cfg = cfg
        self.s = cfg["settings"]
        self.cal = dict(cfg["throttle_cal"], half_width=self.s["throttle_neutral_half_width"])
        self.neutral()
        print("\n" + T("br_reloaded"))
        return self.connect()

    def run(self):
        period = 1.0 / self.s["poll_hz"]
        ok = all(self.devs.get(a) for a in self.needed_aliases())
        last = time.perf_counter()
        last_print = 0.0
        loops, loop_t, loop_hz = 0, time.perf_counter(), 0  # 실제 루프 주기 표시용
        last_retry = 0.0
        last_reload = now = time.perf_counter()
        print("\n" + T("br_running") + "\n")
        while True:
            now = time.perf_counter()
            dt, last = now - last, now
            for ev in pygame.event.get():
                if ev.type == pygame.JOYDEVICEREMOVED:
                    mine = {d.get_instance_id() for d in self.devs.values() if d}
                    if ev.instance_id in mine:
                        self.neutral()
                        print("\n" + T("br_lost"))
                        self.devs = {k: None for k in self.devs}
                        ok = False
                        last_retry = now
                elif ev.type == pygame.JOYDEVICEADDED and not ok:
                    last_retry = 0.0  # 새 장비가 꽂히면 바로 다시 찾기
            if now - last_reload > 1.0:
                last_reload = now
                r = self.reload_if_changed()
                if r is not None:
                    ok = r
            if not ok:
                self.neutral()
                if now - last_retry > 3.0:
                    last_retry = now
                    print("\n" + T("br_searching"))
                    ok = self.connect()
                    if ok:
                        print(T("br_connected"))
                time.sleep(0.05)
                continue
            line = self.step(dt)
            loops += 1
            if now - loop_t >= 1.0:
                loop_hz, loops, loop_t = loops, 0, now
            line = f"{loop_hz}Hz " + line
            if now - last_print > 0.1:
                last_print = now
                print("\r" + line + "\x1b[K", end="", flush=True)  # 줄 끝까지 지우고 덮어쓰기
            time.sleep(max(0.0, period - (time.perf_counter() - now)))


def main():
    os.system("")  # 콘솔 ANSI 제어문자 활성화
    # Windows 기본 대기 정밀도(15.6ms)로는 200Hz 목표가 실제 64Hz로 돈다 → 1ms로 올린다(종료 시 원복)
    winmm = ctypes.WinDLL("winmm")
    winmm.timeBeginPeriod(1)
    try:
        run_bridge()
    finally:
        winmm.timeEndPeriod(1)


def run_bridge():
    cfg = load_config()
    init_pygame()
    print(f"{T('br_title')}  v{VERSION}")
    try:
        bridge = Bridge(cfg)
    except Exception as e:  # ViGEmBus 없음 등
        if "vigem" in (type(e).__name__ + str(e)).lower() or isinstance(e, OSError):
            print(T("br_no_vigem", url="https://github.com/nefarius/ViGEmBus/releases"))
        print(f"({type(e).__name__}: {e})")
        input("Enter")
        return
    if bridge.head:
        if cfg["headtrack"]["source"] == "udp":
            print(T("br_wait_udp", port=cfg["headtrack"]["udp_port"]))
        else:
            print(T("br_wait_ft"))
    try:
        bridge.run()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.neutral()
        del bridge.pad
        pygame.quit()
        print("\n" + T("br_exit"))


if __name__ == "__main__":
    main()
