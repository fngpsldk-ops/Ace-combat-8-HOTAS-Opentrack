# AC8 HOTAS Bridge

Use a **HOTAS (flight stick + throttle)** and **OpenTrack head tracking** in **ACE COMBAT 8**.

AC8 only properly supports Xbox-style controllers. This tool reads your DirectInput stick and throttle and feeds the game a **virtual Xbox 360 controller** (via ViGEmBus). It does not modify game files or inject anything into the game.

```
Stick + Throttle ─┐
                  ├→ Bridge → virtual Xbox 360 pad → AC8
OpenTrack ────────┘   (head tracking → right stick = camera)
```

**Full guide:** [English](release_files/README_en.md) · [한국어](release_files/README_ko.md) · [日本語](release_files/README_ja.md)

## Features

- Works with any DirectInput stick, throttle or pedals (VKB, Virpil, Thrustmaster, Logitech, ...)
- Settings window: click **[Assign]** and press the control. Lamps and live bars show what each control does
- Throttle lever position maps proportionally to LT/RT, with an adjustable cruise (neutral) point. Players without a throttle can use buttons
- Head tracking through OpenTrack's **freetrack 2.0** output (the same profile you use for DCS). Circular mapping, deadzone and anti-deadzone, plus lead to keep up with fast head turns
- Settings saved while the bridge runs apply within 1 second
- UI in Korean, English and Japanese

## Quick start

1. Download the zip from **[Releases](../../releases)** and extract it.
2. Install 64-bit **Python 3.10+** ("Add python.exe to PATH").
3. Run `0_Install.bat`. It pip-installs `pygame-ce` and `vgamepad`, and the ViGEmBus driver setup may appear.
4. Run `1_Settings.bat`, assign your controls, and click **Save**.
5. Run `2_Run_Bridge.bat`, keep it open, and start the game.

If AC8 reacts to your stick even with the bridge closed (seen with Thrustmaster TCA/TWCS), hide the real devices with **HidHide**. See the full guide.

## Project layout

| Path | Purpose |
|---|---|
| `ac8_bridge.py` | Bridge loop: devices + OpenTrack → virtual Xbox 360 pad |
| `ac8_config.py` | Settings window (tkinter) |
| `ac8_common.py` | Shared code: config, device lookup, throttle math, `VERSION` |
| `ac8_i18n.py` | UI strings (ko / en / ja) |
| `release_files/` | Files shipped in the zip: bat files, READMEs, CHANGELOG, requirements |
| `make_release.py` | Builds `dist/AC8_HOTAS_Bridge_v<VERSION>.zip` |
| `check_held.py`, `check_slew.py`, `list_devices.py` | Small diagnostic scripts |

Build a release:

```
python make_release.py
```

## License

[MIT](LICENSE). Anyone may use, modify and redistribute it.

## Credits

- Original approach: Nexus Mods "HOTAS and TrackIR support (instructions)" by cmdrspanky
- Libraries: [pygame-ce](https://github.com/pygame-community/pygame-ce), [vgamepad](https://github.com/yannbouteiller/vgamepad), [ViGEmBus](https://github.com/nefarius/ViGEmBus)
