# AC8 HOTAS Bridge (with head tracking) v1.02

Use a **HOTAS (flight stick and throttle)** and **OpenTrack head tracking** in ACE COMBAT 8.

AC8 only properly supports Xbox-style controllers. This tool reads your stick and throttle and turns them into a **virtual Xbox 360 controller**.
It does not modify game files or inject anything into the game.

```
Stick + Throttle ─┐
                  ├→ Bridge → virtual Xbox 360 pad → AC8
OpenTrack ────────┘   (head tracking → right stick = camera)
```

- Works with any DirectInput stick, throttle or pedals (VKB, Virpil, Thrustmaster, Logitech, ...)
- No throttle? Assign accelerate/decelerate to buttons instead
- Settings window: 한국어 / English / 日本語

## Requirements

| Item | Required | Notes |
|---|---|---|
| Windows 10/11 | yes | |
| 64-bit Python 3.10-3.14 | yes | **Check "Add python.exe to PATH"** in the installer |
| ViGEmBus driver | yes | Its installer appears when you run `0_Install.bat` |
| OpenTrack | optional | Only for head tracking |
| HidHide | depends on device | Needed if the game reacts to your stick even with the bridge closed (see "Hiding real devices from the game") |

**Python compatibility**
- Tested: Python 3.10 and 3.14 (official 64-bit python.org installers).
- 3.11-3.13 and 3.15: expected to work because the required packages support them, but not tested.
- Not supported:
  - Python 3.9 and older
  - 32-bit Python
  - Python for Windows on ARM64 (the virtual pad library only ships x64/x86)
  - free-threaded builds (3.13t/3.14t)
  - Python without tkinter (for example the embeddable package)

## Install

1. Extract the zip anywhere.
2. Run **`0_Install.bat`**. It installs the required packages.
   - If a "ViGEm Bus Driver" setup window appears, finish it, and reboot if asked.
   - If no window appeared and the bridge later says it cannot create the virtual Xbox pad, install ViGEmBus manually:
     https://github.com/nefarius/ViGEmBus/releases

### What `0_Install.bat` does
It does not download anything by itself. It only:
- checks that Python is installed and is 64-bit,
- runs `python -m pip install --upgrade -r requirements.txt`, which installs two packages from PyPI: **pygame-ce 2.5.8** and **vgamepad 0.1.0**.

The vgamepad package ships the official ViGEmBus 1.17.333 installer and may launch it during install. No other driver is involved.
- **New install screen:** click Next and finish it.
- **"Change / Repair / Remove" screen:** the driver is already installed. Click **Cancel**. Choosing Remove uninstalls the driver.

The tool uses **pygame-ce**, a compatible fork of pygame, so it also installs on newer Python versions such as 3.14. `0_Install.bat` removes an old pygame first, because both packages use the same folder and must not be installed together.

### Manual install (without `0_Install.bat`)
1. Install 64-bit Python 3.10-3.14 and tick "Add python.exe to PATH".
2. Install the ViGEmBus driver from GitHub. The latest version is fine. Reboot if asked.
   https://github.com/nefarius/ViGEmBus/releases
3. Open a terminal in the extracted folder and run:
   ```
   python -m pip install pygame-ce==2.5.8 vgamepad==0.1.0
   ```
   If a ViGEmBus setup window opens and you already installed the driver in step 2, you can cancel it.
4. Setup: `python ac8_config.py` (same as `1_Settings.bat`)
5. Run: `python ac8_bridge.py` (same as `2_Run_Bridge.bat`)

### Uninstall
- Delete the folder.
- Optional: `python -m pip uninstall pygame-ce vgamepad`
- Optional: remove "Nefarius Virtual Gamepad Emulation Bus Driver" in Windows Settings > Apps.

## Setup (`1_Settings.bat`)

Connect all your devices first, then run it.

- **Buttons tab:** click **[Assign]** on a row, then press the physical button you want. The lamp on the left lights up while that button is pressed.
  - "Accelerate (button)" and "Decelerate (button)" are for players without a throttle. If you have a throttle, leave them empty and set it up on the Throttle tab.
- **Flight axes tab:** click [Assign], then move the control fully in the shown direction. That direction is saved as +.
  - Required: roll, pitch. Optional: yaw (twist), slew (camera).
- **Throttle tab:**
  1. With the lever fully aft, click [Assign] and push it fully forward. For dual levers, assign both; their average is used.
  2. Calibration: put the lever full aft / full forward / neutral (cruise), and click the matching button each time.
     - Behind neutral the lever drives **LT (decelerate)**, in front of it **RT (accelerate)**, proportionally to position.
     - At neutral the game holds its cruise speed.
- **Head tracking · Sensitivity tab:** change values and click [Save]; a running bridge picks them up immediately.
- Finally, click **[Save]**.

## Run

1. (For head tracking) start OpenTrack and press **Start**.
2. Run **`2_Run_Bridge.bat`**.
3. Keep the bridge window open and launch AC8.
4. When done, press **Ctrl+C** in the bridge window. The virtual pad is cleaned up on exit.

While the bridge runs, anything you save in the Settings window applies within 1 second.

## OpenTrack (head tracking)

- **Output: `freetrack 2.0 Enhanced`**. The same profile you use for DCS and similar games works as is.
- Use whatever input and filter you normally use.
- Set a **Center** shortcut under Options → Shortcuts. Press it while looking straight at the screen to set the camera's reference point.
- The bridge status line shows `HEAD-ON ang…` when it works. If it shows `noHead`, check that OpenTrack is started and the output is set correctly.

## Hiding real devices from the game (HidHide)

Some devices (for example Thrustmaster TCA Airbus and TWCS) are **recognized by AC8 directly**. The game then reads both the real device and the bridge's virtual pad, and inputs get mixed.
- Example: tilting the stick also moves the camera, or throttle button 4 also triggers stick button 4's action.
- Check: **close the bridge, start the game, and move your stick or throttle.** If the game reacts, this is your case. If it still reacts with Steam Input disabled, you need HidHide.

HidHide is made by the same developer as ViGEmBus (Nefarius). It hides the real devices from the game and shows them only to the bridge (python.exe).

1. Install it and reboot: https://github.com/nefarius/HidHide/releases
2. Open **HidHide Configuration Client**.
3. **Applications** tab → **+** → add `python.exe`.
   - Find the path with: `python -c "import sys; print(sys.executable)"`
   - Use that real path, not the python.exe under `WindowsApps` (the Microsoft Store alias).
4. **Devices** tab → tick the stick and throttle to hide.
5. Tick **Enable device hiding**.
6. Open `1_Settings.bat` and check that your devices appear. If it says "No devices found", the python.exe path in step 3 is wrong.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Devices missing in Settings | Check `joy.cpl` (Win+R). If you use **HidHide**, add `python.exe` to its Applications list |
| The game reacts with the bridge closed / inputs get mixed | The game reads the real device directly. Follow "Hiding real devices from the game (HidHide)" above |
| The game ignores the HOTAS | Expected. The game only sees the virtual Xbox pad. Make sure the bridge is running |
| Constantly accelerating or decelerating | Redo the throttle calibration |
| Yaw activates with the twist centered | Raise "Yaw trigger point" |
| Pitch or yaw reversed | Tick "Invert" on the Flight axes tab |
| Camera too sensitive or too sluggish | Change "Head full-scale angle". Smaller is more sensitive |
| Small head moves do nothing, then the camera jumps | Raise "Head anti-deadzone" a little. It compensates for the game's own deadzone |
| Camera overshoots and comes back when you stop | Lower "Lead" |
| A button seems stuck | You may have assigned a latching toggle switch. If the lamp stays lit, pick another button |

## Notes

- Use external controller emulation at your own discretion. The tool works outside the game and doesn't touch game files, but no one can guarantee how anti-cheat or game policies may change.
- ViGEmBus is retired, but it currently works on Windows 10/11.
- Two identical devices (for example two of the same stick) may not be told apart.

## License

MIT License (`LICENSE.txt`). Anyone may use, modify and redistribute it, including commercially. Please include `LICENSE.txt` when you redistribute.

## Credits

- Original approach: Nexus Mods "HOTAS and TrackIR support (instructions)" by cmdrspanky
- Libraries: pygame-ce (LGPL), vgamepad (MIT), ViGEmBus (BSD-3-Clause)
