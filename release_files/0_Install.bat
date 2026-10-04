@echo off
cd /d "%~dp0"
echo === AC8 HOTAS Bridge - Install ===
echo.

python -c "import sys" >nul 2>nul
if errorlevel 1 goto nopython

python -c "import struct,sys; sys.exit(0 if struct.calcsize('P')==8 else 1)"
if errorlevel 1 goto not64

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto tooold

python -c "import tkinter" >nul 2>nul
if errorlevel 1 goto notk

rem pygame and pygame-ce share the "pygame" folder; remove the old one first
python -m pip uninstall -y pygame >nul 2>nul

echo NOTE: A "ViGEm Bus Driver" setup window may open during install.
echo       - New install screen: click Next and finish it.
echo       - "Change / Repair / Remove" screen: the driver is already installed. Click Cancel.
echo.
python -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto pipfail

echo.
python -c "from ac8_i18n import T; print(T('inst_done'))"
echo.
pause
exit /b 0

:nopython
echo [!] Python was not found.
echo     Install 64-bit Python 3.10 or newer and tick "Add python.exe to PATH",
echo     then run this file again.
start "" https://www.python.org/downloads/windows/
pause
exit /b 1

:not64
echo [!] 64-bit Python is required. Please install the 64-bit version.
pause
exit /b 1

:tooold
echo [!] Python 3.10 or newer is required. Your version:
python --version
start "" https://www.python.org/downloads/windows/
pause
exit /b 1

:notk
echo [!] This Python has no tkinter (needed for the settings window).
echo     Reinstall Python from python.org and keep "tcl/tk and IDLE" checked.
pause
exit /b 1

:pipfail
echo [!] Package install failed. Check your internet connection and try again.
pause
exit /b 1
