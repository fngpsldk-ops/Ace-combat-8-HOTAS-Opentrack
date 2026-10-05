"""AC8 HOTAS 설정 창 (GUI, 한국어/English/日本語).

줄마다 [입력]을 누르고 쓸 물리 버튼/축을 조작하면 지정된다. [저장]하면 config.json에 쓰고,
실행 중인 브리지는 1초 안에 다시 읽는다.
"""
import copy
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

import ac8_i18n
from ac8_common import (ACTIONS, CONFIG_PATH, DEFAULT_HEADTRACK, DEFAULT_SETTINGS, VERSION, action_label,
                        find_device, init_pygame, pygame, split_throttle, xbox_label)
from ac8_i18n import LANGS, T

FONTS = {"ko": "Malgun Gothic", "ja": "Yu Gothic UI", "en": "Segoe UI"}
ON_COLOR = "#2e9e4f"
OFF_COLOR = "#d9d9d9"

# 키, Xbox 출력, 게임 동작, 입력 안내(이 방향이 +) — 모두 번역 키
AXES = [
    ("roll", "xbox_lx", "axis_roll", "hint_roll"),
    ("pitch", "xbox_ly", "axis_pitch", "hint_pitch"),
    ("yaw", None, "axis_yaw", "hint_yaw"),
    ("slew_x", "xbox_rx", "axis_slew_x", "hint_slew_x"),
    ("slew_y", "xbox_ry", "axis_slew_y", "hint_slew_y"),
]

# 구역, 키, 표시명(번역 키), 최소, 최대, 간격
NUMBERS = [
    ("settings", "roll_deadzone", "n_roll_dz", 0.0, 0.5, 0.01),
    ("settings", "pitch_deadzone", "n_pitch_dz", 0.0, 0.5, 0.01),
    ("settings", "stick_gain", "n_stick_gain", 0.5, 3.0, 0.05),
    ("settings", "stick_exponent", "n_stick_exp", 0.3, 3.0, 0.05),
    ("settings", "stick_anti_deadzone", "n_stick_adz", 0.0, 0.6, 0.01),
    ("settings", "yaw_threshold", "n_yaw_th", 0.02, 0.9, 0.01),
    ("settings", "slew_deadzone", "n_slew_dz", 0.0, 0.9, 0.01),
    ("headtrack", "yaw_full_scale_deg", "n_yaw_fs", 10.0, 180.0, 1.0),
    ("headtrack", "pitch_full_scale_deg", "n_pitch_fs", 5.0, 90.0, 1.0),
    ("headtrack", "deadzone_deg", "n_head_dz", 0.0, 10.0, 0.05),
    ("headtrack", "anti_deadzone", "n_head_adz", 0.0, 0.6, 0.01),
    ("headtrack", "yaw_exponent", "n_head_exp", 0.3, 3.0, 0.05),
    ("headtrack", "lead_sec", "n_lead", 0.0, 0.5, 0.01),
    ("headtrack", "lead_min_speed", "n_lead_min", 0.0, 200.0, 1.0),
    ("headtrack", "smoothing_sec", "n_smooth", 0.0, 0.5, 0.01),
]


def default_config():
    return {"devices": {}, "axes": {"throttle": []}, "throttle_cal": {"aft": -1.0, "forward": 1.0, "neutral": 0.0},
            "buttons": {}, "hat": None, "settings": dict(DEFAULT_SETTINGS), "headtrack": dict(DEFAULT_HEADTRACK)}


def is_virtual(dev):
    # 브리지가 만든 가상 Xbox 패드는 입력 후보에서 뺀다
    name = dev.get_name().lower()
    return "xbox 360" in name or "xinput" in name


class App:
    def __init__(self, root):
        self.root = root
        self.cfg = self.load()
        self.devs = []
        self.capture = None
        self.dirty = False
        self.status = tk.StringVar()
        self.refresh_devices()
        root.bind("<Escape>", lambda e: self.cancel_capture())
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.build_ui()
        self.set_status(self.device_status() + ("  " + T("start_hint") if self.devs else ""))
        root.after(20, self.tick)

    # ---------- 설정/장비 ----------
    def load(self):
        cfg = default_config()
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                loaded = json.load(f)
            cfg.update(loaded)
            cfg["settings"] = {**DEFAULT_SETTINGS, **loaded.get("settings", {})}
            cfg["headtrack"] = {**DEFAULT_HEADTRACK, **loaded.get("headtrack", {})}
        cfg["axes"].setdefault("throttle", [])
        return cfg

    def refresh_devices(self):
        pygame.event.pump()
        devs = []
        for i in range(pygame.joystick.get_count()):
            d = pygame.joystick.Joystick(i)
            d.init()
            if not is_virtual(d):
                devs.append(d)
        self.devs = devs
        self.set_status(self.device_status())

    def device_status(self):
        if not self.devs:
            return T("no_devices")  # HidHide가 python.exe를 숨기는 경우가 많다
        return T("devices_found", n=len(self.devs), names=", ".join(d.get_name() for d in self.devs))

    def dev_for(self, alias):
        info = self.cfg["devices"].get(alias)
        return find_device(self.devs, info) if info else None

    def alias_for(self, dev, preferred=None):
        for alias, info in self.cfg["devices"].items():
            if find_device(self.devs, info) is dev:
                info.update(guid=dev.get_guid(), name=dev.get_name())  # 옛 GUID면 지금 값으로 갱신
                return alias
        alias = preferred if preferred and preferred not in self.cfg["devices"] else None
        n = 1
        while not alias:
            cand = f"dev{n}"
            alias = cand if cand not in self.cfg["devices"] else None
            n += 1
        self.cfg["devices"][alias] = {"guid": dev.get_guid(), "name": dev.get_name()}
        return alias

    def short_name(self, alias):
        name = self.cfg["devices"].get(alias, {}).get("name", alias)
        return name if len(name) <= 24 else name[:23] + "…"

    def read_axis(self, entry):
        if not entry:
            return None
        d = self.dev_for(entry["dev"])
        if not d or entry["axis"] >= d.get_numaxes():
            return None
        v = d.get_axis(entry["axis"])
        return -v if entry.get("invert") else v

    # ---------- UI 구성 ----------
    def build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        font = (FONTS.get(ac8_i18n._lang, "Segoe UI"), 10)
        self.font, self.bold = font, (font[0], 10, "bold")
        self.root.option_add("*Font", font)
        ttk.Style().configure(".", font=font)
        self.root.title(f"{T('title')}  v{VERSION}")
        self.rows = {}

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=(8, 0))
        self.lang_var = tk.StringVar(value=dict(LANGS)[ac8_i18n._lang])
        lang = ttk.Combobox(top, textvariable=self.lang_var, values=[n for _, n in LANGS], state="readonly", width=10)
        lang.pack(side="right")
        lang.bind("<<ComboboxSelected>>", self.change_lang)
        ttk.Label(top, text=T("language") + " / Language").pack(side="right", padx=6)

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.build_buttons(self.tab(nb, T("tab_buttons")))
        self.build_axes(self.tab(nb, T("tab_axes")))
        self.build_throttle(self.tab(nb, T("tab_throttle")))
        self.build_numbers(self.tab(nb, T("tab_head")))

        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(bottom, text=T("save"), command=self.save).pack(side="right")
        ttk.Button(bottom, text=T("rescan"), command=self.refresh_devices).pack(side="right", padx=6)
        ttk.Label(bottom, textvariable=self.status, foreground="#555", wraplength=620).pack(side="left")
        self.refresh_labels()

    def change_lang(self, _event=None):
        code = next(c for c, n in LANGS if n == self.lang_var.get())
        if code == ac8_i18n._lang:
            return
        self.collect_numbers(self.cfg)  # 저장 안 한 숫자 입력도 유지
        self.capture = None
        ac8_i18n.set_lang(code)
        self.build_ui()
        self.set_status("")

    def tab(self, nb, title):
        f = ttk.Frame(nb, padding=10)
        nb.add(f, text=title)
        return f

    def header(self, parent, cols):
        for c, text in enumerate(cols):
            ttk.Label(parent, text=text, font=self.bold).grid(row=0, column=c, sticky="w", padx=4, pady=(0, 6))

    def build_buttons(self, f):
        self.header(f, ["", T("col_xbox"), T("col_action"), T("col_input"), "", ""])
        r = 1
        for key, xbox in ACTIONS:
            self.button_row(f, r, key, xbox_label(xbox), action_label(key), "button")
            r += 1
            if key == "throttle_down":
                # 가속/감속 버튼은 스로틀이 없는 사람용
                ttk.Label(f, text=T("throttle_btn_note"), foreground="#666").grid(
                    row=r, column=1, columnspan=5, sticky="w", pady=(0, 6))
                r += 1
        self.button_row(f, r, "__hat", T("xbox_dpad"), T("act_hat"), "hat")

    def button_row(self, f, r, key, xbox, label, kind):
        lamp = tk.Label(f, width=2, bg=OFF_COLOR)
        lamp.grid(row=r, column=0, padx=(0, 6), pady=2)
        ttk.Label(f, text=xbox, width=13).grid(row=r, column=1, sticky="w")
        ttk.Label(f, text=label, width=26).grid(row=r, column=2, sticky="w")
        var = tk.StringVar()
        ttk.Label(f, textvariable=var, width=36).grid(row=r, column=3, sticky="w")
        ttk.Button(f, text=T("assign"), width=7, command=lambda: self.start_capture(kind, key)).grid(row=r, column=4, padx=2)
        ttk.Button(f, text=T("clear"), width=7, command=lambda: self.clear(kind, key)).grid(row=r, column=5, padx=2)
        self.rows[key] = {"var": var, "lamp": lamp, "kind": kind}

    def build_axes(self, f):
        self.header(f, [T("col_xbox"), T("col_action"), T("col_axis"), T("col_value"), "", T("col_invert"), ""])
        for r, (key, xbox, label, _) in enumerate(AXES, start=1):
            ttk.Label(f, text=T(xbox) if xbox else "LB / RB", width=13).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Label(f, text=T(label), width=22).grid(row=r, column=1, sticky="w")
            var = tk.StringVar()
            ttk.Label(f, textvariable=var, width=32).grid(row=r, column=2, sticky="w")
            bar = tk.Canvas(f, width=160, height=14, bg="#f4f4f4", highlightthickness=1, highlightbackground="#bbb")
            bar.grid(row=r, column=3, padx=4)
            ttk.Button(f, text=T("assign"), width=7, command=lambda k=key: self.start_capture("axis", k)).grid(row=r, column=4, padx=2)
            inv = tk.BooleanVar()
            ttk.Checkbutton(f, variable=inv, command=lambda k=key, v=inv: self.set_invert(k, v)).grid(row=r, column=5)
            ttk.Button(f, text=T("clear"), width=7, command=lambda k=key: self.clear("axis", k)).grid(row=r, column=6, padx=2)
            self.rows[key] = {"var": var, "bar": bar, "inv": inv, "kind": "axis"}
        ttk.Label(f, text=T("axes_hint"), foreground="#666").grid(row=len(AXES) + 1, column=0, columnspan=7,
                                                                   sticky="w", pady=(10, 0))

    def build_throttle(self, f):
        self.header(f, [T("col_lever"), T("col_axis"), T("col_value"), "", T("col_invert"), ""])
        for i in range(2):
            r = i + 1
            key = f"__lever{i}"
            ttk.Label(f, text=T(f"lever_{i}"), width=12).grid(row=r, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            ttk.Label(f, textvariable=var, width=32).grid(row=r, column=1, sticky="w")
            bar = tk.Canvas(f, width=160, height=14, bg="#f4f4f4", highlightthickness=1, highlightbackground="#bbb")
            bar.grid(row=r, column=2, padx=4)
            ttk.Button(f, text=T("assign"), width=7, command=lambda k=key: self.start_capture("lever", k)).grid(row=r, column=3, padx=2)
            inv = tk.BooleanVar()
            ttk.Checkbutton(f, variable=inv, command=lambda idx=i, v=inv: self.set_lever_invert(idx, v)).grid(row=r, column=4)
            ttk.Button(f, text=T("clear"), width=7, command=lambda k=key: self.clear("lever", k)).grid(row=r, column=5, padx=2)
            self.rows[key] = {"var": var, "bar": bar, "inv": inv, "kind": "lever"}
        ttk.Label(f, text=T("lever_hint"), foreground="#666", justify="left").grid(row=3, column=0, columnspan=6,
                                                                                  sticky="w", pady=(6, 12))

        cal = ttk.LabelFrame(f, text=T("cal_frame"), padding=8)
        cal.grid(row=4, column=0, columnspan=6, sticky="we")
        self.cal_var = tk.StringVar()
        for c, (key, which) in enumerate([("cal_aft", "aft"), ("cal_fwd", "forward"),
                                          ("cal_neutral", "neutral"), ("cal_center", "center")]):
            ttk.Button(cal, text=T(key), command=lambda w=which: self.set_cal(w)).grid(row=0, column=c, padx=3, pady=3)
        ttk.Label(cal, textvariable=self.cal_var).grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ttk.Label(cal, text=T("neutral_width")).grid(row=2, column=0, sticky="e", pady=(8, 0))
        self.width_var = tk.DoubleVar(value=round(self.cfg["settings"]["throttle_neutral_half_width"] * 100, 1))
        ttk.Spinbox(cal, from_=0, to=30, increment=0.5, textvariable=self.width_var, width=7,
                    command=self.mark_dirty).grid(row=2, column=1, sticky="w", pady=(8, 0))

        out = ttk.LabelFrame(f, text=T("output_frame"), padding=8)
        out.grid(row=5, column=0, columnspan=6, sticky="we", pady=(10, 0))
        self.thr_text = tk.StringVar()
        ttk.Label(out, textvariable=self.thr_text).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(out, text=T("lt_label")).grid(row=1, column=0, sticky="e")
        self.lt_bar = ttk.Progressbar(out, length=260, maximum=1.0)
        self.lt_bar.grid(row=1, column=1, padx=6, pady=2)
        ttk.Label(out, text=T("rt_label")).grid(row=2, column=0, sticky="e")
        self.rt_bar = ttk.Progressbar(out, length=260, maximum=1.0)
        self.rt_bar.grid(row=2, column=1, padx=6, pady=2)

    def build_numbers(self, f):
        ht = self.cfg["headtrack"]
        self.ht_enabled = tk.BooleanVar(value=ht["enabled"])
        self.inv_x = tk.BooleanVar(value=ht["invert_x"])
        self.inv_y = tk.BooleanVar(value=ht["invert_y"])
        top = ttk.Frame(f)
        top.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Checkbutton(top, text=T("ht_enable"), variable=self.ht_enabled, command=self.mark_dirty).pack(side="left")
        ttk.Checkbutton(top, text=T("inv_x"), variable=self.inv_x, command=self.mark_dirty).pack(side="left", padx=10)
        ttk.Checkbutton(top, text=T("inv_y"), variable=self.inv_y, command=self.mark_dirty).pack(side="left")
        self.num_vars = {}
        for r, (sec, key, label, lo, hi, step) in enumerate(NUMBERS, start=1):
            ttk.Label(f, text=T(label)).grid(row=r, column=0, sticky="e", padx=(0, 8), pady=2)
            var = tk.DoubleVar(value=self.cfg[sec][key])
            sp = ttk.Spinbox(f, from_=lo, to=hi, increment=step, textvariable=var, width=8, command=self.mark_dirty)
            sp.grid(row=r, column=1, sticky="w")
            sp.bind("<KeyRelease>", lambda e: self.mark_dirty())
            self.num_vars[(sec, key)] = var
        ttk.Label(f, text=T("ht_note"), foreground="#666").grid(row=len(NUMBERS) + 1, column=0, columnspan=2,
                                                                 sticky="w", pady=(10, 0))

    # ---------- 표시 ----------
    def set_status(self, text):
        self.status.set(text)

    def mark_dirty(self):
        self.dirty = True
        self.set_status(T("dirty"))

    def describe_button(self, b):
        return T("desc_button", dev=self.short_name(b["dev"]), n=b["button"] + 1) if b else "—"

    def describe_axis(self, a):
        return T("desc_axis", dev=self.short_name(a["dev"]), n=a["axis"] + 1) if a else "—"

    def lever(self, i):
        lv = self.cfg["axes"]["throttle"]
        return lv[i] if i < len(lv) else None

    def refresh_labels(self):
        for key, _ in ACTIONS:
            self.rows[key]["var"].set(self.describe_button(self.cfg["buttons"].get(key)))
        h = self.cfg.get("hat")
        self.rows["__hat"]["var"].set(T("desc_hat", dev=self.short_name(h["dev"]), n=h["hat"] + 1) if h else "—")
        for key, *_ in AXES:
            a = self.cfg["axes"].get(key)
            self.rows[key]["var"].set(self.describe_axis(a))
            self.rows[key]["inv"].set(bool(a and a.get("invert")))
        for i in range(2):
            lv = self.lever(i)
            self.rows[f"__lever{i}"]["var"].set(self.describe_axis(lv))
            self.rows[f"__lever{i}"]["inv"].set(bool(lv and lv.get("invert")))
        c = self.cfg["throttle_cal"]
        self.cal_var.set(T("cal_values", aft=f"{c['aft']:+.3f}", neutral=f"{c['neutral']:+.3f}",
                           fwd=f"{c['forward']:+.3f}"))

    def draw_bar(self, canvas, v):
        canvas.delete("all")
        w, h = 160, 14
        canvas.create_line(w / 2, 0, w / 2, h, fill="#999")
        if v is None:
            return
        x = w / 2 + max(-1.0, min(1.0, v)) * (w / 2 - 1)
        canvas.create_rectangle(min(w / 2, x), 2, max(w / 2, x), h - 1, fill="#3a7bd5", outline="")

    def throttle_raw(self):
        vals = [v for v in (self.read_axis(lv) for lv in self.cfg["axes"]["throttle"]) if v is not None]
        return sum(vals) / len(vals) if vals else None

    # ---------- 입력 받기 ----------
    def snapshot(self):
        return {"axes": {(i, a): d.get_axis(a) for i, d in enumerate(self.devs) for a in range(d.get_numaxes())},
                "buttons": {(i, b): d.get_button(b) for i, d in enumerate(self.devs) for b in range(d.get_numbuttons())}}

    def start_capture(self, kind, key):
        pygame.event.pump()
        self.capture = {"kind": kind, "key": key, "base": self.snapshot()}
        if kind == "button":
            msg = T("cap_button")
        elif kind == "hat":
            msg = T("cap_hat")
        elif kind == "axis":
            msg = "▶ " + T(next(a[3] for a in AXES if a[0] == key))
        else:
            msg = T("cap_lever")
        self.rows[key]["var"].set(msg)
        self.set_status(msg + "  " + T("esc_cancel"))

    def cancel_capture(self):
        if self.capture:
            self.capture = None
            self.refresh_labels()
            self.set_status(T("cancelled"))

    def poll_capture(self):
        c = self.capture
        kind, key, base = c["kind"], c["key"], c["base"]
        if kind == "button":
            for (i, b), was in base["buttons"].items():
                now = self.devs[i].get_button(b) if i < len(self.devs) else 0
                if now and not was:
                    entry = {"dev": self.alias_for(self.devs[i]), "button": b}
                    # 같은 물리 버튼이 다른 동작에 있으면 알려준다
                    dup = [k for k, v in self.cfg["buttons"].items() if v == entry and k != key]
                    self.cfg["buttons"][key] = entry
                    msg = T("assigned", what=self.describe_button(entry))
                    if dup:
                        msg += T("dup_warn", other=action_label(dup[0]))
                    self.finish(msg)
                    return
                base["buttons"][(i, b)] = now
        elif kind == "hat":
            for d in self.devs:
                for h in range(d.get_numhats()):
                    if d.get_hat(h) != (0, 0):
                        self.cfg["hat"] = {"dev": self.alias_for(d), "hat": h}
                        self.finish(T("assigned", what=T("desc_hat", dev=d.get_name(), n=h + 1)))
                        return
        else:
            best, delta = None, 0.0
            for (i, a), b in base["axes"].items():
                if i < len(self.devs):
                    dv = self.devs[i].get_axis(a) - b
                    if abs(dv) > abs(delta):
                        best, delta = (i, a), dv
            if best and abs(delta) >= 0.6:
                i, a = best
                pref = "throttle" if kind == "lever" else ("stick" if key in ("roll", "pitch", "yaw") else None)
                entry = {"dev": self.alias_for(self.devs[i], pref), "axis": a, "invert": delta < 0}
                if kind == "axis":
                    self.cfg["axes"][key] = entry
                else:
                    idx = int(key[-1])
                    levers = self.cfg["axes"]["throttle"]
                    while len(levers) <= idx:
                        levers.append(None)
                    levers[idx] = entry
                self.finish(T("assigned", what=self.describe_axis(entry)) + "  ("
                            + T("invert_state", state=T("on" if delta < 0 else "off")) + ")")

    def finish(self, msg):
        self.capture = None
        self.refresh_labels()
        self.dirty = True
        self.set_status(msg + T("press_save"))

    def clear(self, kind, key):
        self.capture = None
        if kind == "button":
            self.cfg["buttons"].pop(key, None)
        elif kind == "hat":
            self.cfg["hat"] = None
        elif kind == "axis":
            self.cfg["axes"][key] = None
        else:
            idx = int(key[-1])
            levers = self.cfg["axes"]["throttle"]
            if idx < len(levers):
                levers[idx] = None  # 칸 위치(왼쪽/오른쪽)는 유지
        self.refresh_labels()
        self.mark_dirty()

    def set_invert(self, key, var):
        a = self.cfg["axes"].get(key)
        if a:
            a["invert"] = var.get()
            self.mark_dirty()
        else:
            var.set(False)

    def set_lever_invert(self, idx, var):
        lv = self.lever(idx)
        if lv:
            lv["invert"] = var.get()
            self.mark_dirty()
        else:
            var.set(False)

    def set_cal(self, which):
        c = self.cfg["throttle_cal"]
        if which == "center":
            c["neutral"] = (c["aft"] + c["forward"]) / 2
        else:
            v = self.throttle_raw()
            if v is None:
                messagebox.showwarning(T("tab_throttle"), T("lever_first"))
                return
            c[which] = v
        self.refresh_labels()
        self.mark_dirty()

    # ---------- 주기 처리 ----------
    def tick(self):
        try:
            self.update_live()
        except tk.TclError:  # 언어 변경으로 위젯을 다시 만드는 중
            pass
        self.root.after(30, self.tick)

    def update_live(self):
        for ev in pygame.event.get():
            if ev.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self.refresh_devices()
        if self.capture:
            self.poll_capture()
        for key, _ in ACTIONS:
            b = self.cfg["buttons"].get(key)
            d = self.dev_for(b["dev"]) if b else None
            on = bool(d and b["button"] < d.get_numbuttons() and d.get_button(b["button"]))
            self.rows[key]["lamp"].configure(bg=ON_COLOR if on else OFF_COLOR)
        h = self.cfg.get("hat")
        d = self.dev_for(h["dev"]) if h else None
        on = bool(d and h["hat"] < d.get_numhats() and d.get_hat(h["hat"]) != (0, 0))
        self.rows["__hat"]["lamp"].configure(bg=ON_COLOR if on else OFF_COLOR)
        for key, *_ in AXES:
            self.draw_bar(self.rows[key]["bar"], self.read_axis(self.cfg["axes"].get(key)))
        for i in range(2):
            self.draw_bar(self.rows[f"__lever{i}"]["bar"], self.read_axis(self.lever(i)))
        raw = self.throttle_raw()
        if raw is None:
            self.thr_text.set(T("lever_none"))
            self.lt_bar["value"] = self.rt_bar["value"] = 0
        else:
            try:
                hw = float(self.width_var.get()) / 100
            except (tk.TclError, ValueError):
                hw = self.cfg["settings"]["throttle_neutral_half_width"]
            lt, rt = split_throttle(raw, dict(self.cfg["throttle_cal"], half_width=hw))
            self.thr_text.set(T("lever_out", raw=f"{raw:+.3f}", lt=f"{lt * 100:.0f}", rt=f"{rt * 100:.0f}"))
            self.lt_bar["value"], self.rt_bar["value"] = lt, rt

    # ---------- 저장 ----------
    def collect_numbers(self, cfg):
        """숫자/체크 입력을 cfg에 옮긴다. 잘못된 숫자는 ValueError."""
        for (sec, key), var in self.num_vars.items():
            try:
                cfg[sec][key] = float(var.get())
            except (tk.TclError, ValueError):
                raise ValueError(key)
        # 공통 커브: 상하도 같은 값
        cfg["headtrack"]["pitch_exponent"] = cfg["headtrack"]["yaw_exponent"]
        try:
            cfg["settings"]["throttle_neutral_half_width"] = float(self.width_var.get()) / 100
        except (tk.TclError, ValueError):
            raise ValueError("throttle_neutral_half_width")
        cfg["headtrack"]["enabled"] = self.ht_enabled.get()
        cfg["headtrack"]["invert_x"] = self.inv_x.get()
        cfg["headtrack"]["invert_y"] = self.inv_y.get()

    def save(self):
        cfg = copy.deepcopy(self.cfg)
        try:
            self.collect_numbers(cfg)
        except ValueError:
            messagebox.showerror(T("save_fail"), T("bad_number"))
            return
        cfg["axes"]["throttle"] = [lv for lv in cfg["axes"]["throttle"] if lv]
        cfg["throttle_cal"]["half_width"] = cfg["settings"]["throttle_neutral_half_width"]
        missing = [T(k) for k in ("axis_roll", "axis_pitch") if not cfg["axes"].get(k[5:])]
        if missing:
            messagebox.showerror(T("save_fail"), T("missing", items=", ".join(missing)))
            return
        # 지정에 쓰이지 않는 장비는 목록에서 정리
        used = {cfg["axes"][k]["dev"] for k in cfg["axes"] if k != "throttle" and cfg["axes"][k]}
        used |= {lv["dev"] for lv in cfg["axes"]["throttle"]}
        used |= {b["dev"] for b in cfg["buttons"].values()}
        if cfg.get("hat"):
            used.add(cfg["hat"]["dev"])
        cfg["devices"] = {k: v for k, v in cfg["devices"].items() if k in used}
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_PATH)  # 브리지가 반쯤 쓴 파일을 읽지 않도록 한 번에 교체
        self.cfg = cfg
        self.dirty = False
        self.set_status(T("saved"))

    def on_close(self):
        if self.dirty and not messagebox.askyesno(T("close"), T("close_unsaved")):
            return
        self.root.destroy()


def main():
    init_pygame()
    root = tk.Tk()
    App(root)
    root.mainloop()
    pygame.quit()


if __name__ == "__main__":
    main()
