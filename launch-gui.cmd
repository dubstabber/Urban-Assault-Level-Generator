@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%" || (
    echo Could not open project folder: "%ROOT%"
    pause
    exit /b 1
)

set "PYTHONPATH=%ROOT%src"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 -m ualg.gui
    set "EXIT_CODE=%ERRORLEVEL%"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Python was not found. Install Python 3.11 or newer and try again.
        pause
        exit /b 1
    )
    python -m ualg.gui
    set "EXIT_CODE=%ERRORLEVEL%"
)

if not "%EXIT_CODE%"=="0" (
    echo.
    echo GUI exited with error code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
