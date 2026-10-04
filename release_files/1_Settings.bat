@echo off
cd /d "%~dp0"
python ac8_config.py
if errorlevel 1 pause
