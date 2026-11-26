@echo off
cd /d "%~dp0"
py -3.11 build_native.py
set result=%errorlevel%
if not "%result%"=="0" echo Build failed. See BUILD-ERROR.txt above or Python launcher message.
pause
exit /b %result%
