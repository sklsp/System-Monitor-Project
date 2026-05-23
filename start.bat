@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title System Monitor - Launcher
color 0A

echo.
echo  ============================================
echo    System Monitor - Automatic Setup and Run
echo  ============================================
echo.

REM --- Find Python ---
set "PYCMD="
where python >nul 2>&1 && set "PYCMD=python"
if not defined PYCMD (
    where py >nul 2>&1 && set "PYCMD=py -3"
)

if not defined PYCMD (
    echo  [ERROR] Python was not found on this PC.
    echo.
    echo  Install Python from https://www.python.org/downloads/
    echo  Important: check "Add python.exe to PATH" during install.
    echo  Then restart your PC and run this file again.
    echo.
    pause
    exit /b 1
)

echo  Using: %PYCMD%
%PYCMD% --version
if errorlevel 1 (
    echo.
    echo  [ERROR] Python is installed but not working correctly.
    pause
    exit /b 1
)

REM --- Virtual environment ---
set "VENV_PY=%~dp0.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo.
    echo  First run: creating virtual environment...
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo.
        echo  [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
)

REM --- Dependencies ---
"%VENV_PY%" -c "import PyQt5, psutil" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  First run: installing required packages...
    echo  This can take a few minutes. Please wait.
    echo.
    "%VENV_PY%" -m pip install --upgrade pip
    if errorlevel 1 (
        echo  [ERROR] Failed to upgrade pip.
        pause
        exit /b 1
    )
    "%VENV_PY%" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo.
        echo  [ERROR] Failed to install packages from requirements.txt
        pause
        exit /b 1
    )
    echo.
    echo  Packages installed successfully.
)

echo.
echo  Starting System Monitor...
echo  You can close this window after the app opens.
echo  If the app crashes, an error message will stay visible here.
echo.

"%VENV_PY%" "%~dp0main.py"
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo.
    echo  [ERROR] The application exited with code %EXITCODE%.
    echo  Read any red error text above, or ask for help with that message.
    echo.
    pause
    exit /b %EXITCODE%
)

endlocal
exit /b 0
