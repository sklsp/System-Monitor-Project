@echo off
:: Start System Monitor with administrator rights (needed for CPU temp on many gaming PCs).
cd /d "%~dp0"
powershell -NoProfile -Command "Start-Process -FilePath '%~dp0start.bat' -Verb RunAs -WorkingDirectory '%~dp0'"
