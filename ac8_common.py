"""AC8 HOTAS 브리지 공용 코드: 설정 파일, 장비 찾기, 축 변환."""
import json
import os
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
# 창이 없어도(게임이 포커스를 가져가도) 조이스틱 입력을 계속 받는다.
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
import pygame  # noqa: E402

VERSION = "1.03"  # 배포 버전. make_release.py가 zip 이름에 쓴다

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")

from ac8_i18n import T  # noqa: E402

# 버튼으로 지정할 수 있는 동작. (키, Xbox 출력 표기) — '@'로 시작하면 번역 키
ACTIONS = [
    ("gun", "A"),
    ("missile", "B"),
    ("weapon", "X"),
    ("target", "Y"),
    ("boresight", "@xbox_ls"),
    ("camera", "@xbox_rs"),
    ("map", "Back"),
    ("pause", "Start"),
    ("autopilot", "LB+RB"),
    ("flare", "LS+RS"),
    ("highg", "LT+RT"),
    ("throttle_up", "RT"),
    ("throttle_down", "LT"),
    ("head_toggle", "@xbox_bridge"),
]


def action_label(key):
    return T("act_" + key)


def xbox_label(text):
    return T(text[1:]) if text.startswith("@") else text

DEFAULT_SETTINGS = {
    "poll_hz": 200,
    "roll_deadzone": 0.03,
    "pitch_deadzone": 0.03,
    "yaw_threshold": 0.18,
    # 스로틀 중립 구간 폭(전체 행정 대비 비율의 절반). 중립점 ± 이 값.
    "throttle_neutral_half_width": 0.08,
    "slew_deadzone": 0.15,
    # 롤/피치 반응: 배율(>1이면 끝까지 안 젖혀도 최대), 커브(<1이면 중앙이 예민), 안티 데드존(게임 데드존 건너뛰기)
    "stick_gain": 1.0,
    "stick_exponent": 1.0,
    "stick_anti_deadzone": 0.0,
}

DEFAULT_HEADTRACK = {
    "enabled": False,
    # "freetrack": OpenTrack freetrack 2.0 출력(공유 메모리), "udp": UDP over network 출력
    "source": "freetrack",
    "udp_port": 4243,
    "yaw_full_scale_deg": 75.0,
    "pitch_full_scale_deg": 15.0,
    "deadzone_deg": 0.0,
    "anti_deadzone": 0.0,
    "lead_sec": 0.0,
    "lead_min_speed": 15.0,  # °/s
    "yaw_exponent": 1.0,
    "pitch_exponent": 1.0,
    "invert_x": False,
    "invert_y": False,
    "smoothing_sec": 0.08,
    "stale_timeout_sec": 0.25,
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(T("br_no_config"))
        input("Enter")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["settings"] = {**DEFAULT_SETTINGS, **cfg.get("settings", {})}
    cfg["headtrack"] = {**DEFAULT_HEADTRACK, **cfg.get("headtrack", {})}
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def init_pygame():
    pygame.init()
    pygame.joystick.init()


def open_all():
    """현재 연결된 모든 조이스틱을 열어 리스트로 반환."""
    devs = []
    for i in range(pygame.joystick.get_count()):
        d = pygame.joystick.Joystick(i)
        d.init()
        devs.append(d)
    return devs


def guid_key(guid):
    """SDL GUID에서 이름 CRC(16진 4~7자리)를 뺀 값. CRC는 SDL 버전마다 달라질 수 있다
    (같은 VKB 스틱이 pygame 2.6.1=03006cad…, pygame-ce 2.5.8=03005fcf…)."""
    return guid[:4] + guid[8:]


def find_device(devs, info):
    """설정의 {guid, name}과 일치하는 장비. GUID → CRC 뺀 GUID → 유일한 이름 순서로 찾는다."""
    for d in devs:
        if d.get_guid() == info["guid"]:
            return d
    key = guid_key(info["guid"])
    same_key = [d for d in devs if guid_key(d.get_guid()) == key]
    if len(same_key) == 1:
        return same_key[0]
    same_name = [d for d in (same_key or devs) if d.get_name() == info["name"]]
    return same_name[0] if len(same_name) == 1 else None


def clamp(v, lo=-1.0, hi=1.0):
    return max(lo, min(hi, v))


def rescaled_deadzone(v, size):
    v = clamp(v)
    if abs(v) <= size:
        return 0.0
    sign = 1.0 if v > 0 else -1.0
    return sign * (abs(v) - size) / (1.0 - size)


def shape_axis(v, deadzone, gain=1.0, exponent=1.0, anti_deadzone=0.0):
    """비행 축: 데드존(재스케일) → 커브 → 배율 → 안티 데드존. 결과는 -1~1."""
    v = rescaled_deadzone(v, deadzone)
    if v == 0.0:
        return 0.0
    m = min(1.0, abs(v) ** exponent * gain)
    m = anti_deadzone + (1.0 - anti_deadzone) * m
    return m if v > 0 else -m


def signed_power(v, e):
    if v == 0.0:
        return 0.0
    return (1.0 if v > 0 else -1.0) * abs(v) ** e


def split_throttle(raw, cal):
    """물리 스로틀 값 → (LT 감속, RT 가속). cal은 aft/neutral/forward 원시값."""
    aft, fwd, neutral = cal["aft"], cal["forward"], cal["neutral"]
    half = cal["half_width"]
    # 앞으로 밀수록 값이 커지도록 정규화
    if fwd < aft:
        raw, aft, fwd, neutral = -raw, -aft, -fwd, -neutral
    span = fwd - aft
    if span <= 1e-6:
        return 0.0, 0.0
    lo = neutral - half * span
    hi = neutral + half * span
    if raw < lo:
        denom = lo - aft
        return (clamp((lo - raw) / denom, 0.0, 1.0) if denom > 1e-6 else 1.0), 0.0
    if raw > hi:
        denom = fwd - hi
        return 0.0, (clamp((raw - hi) / denom, 0.0, 1.0) if denom > 1e-6 else 1.0)
    return 0.0, 0.0
