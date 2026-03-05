@echo off
REM Stop AI Employee System (Windows Batch)
REM Stops all watcher scripts

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PID_DIR=%SCRIPT_DIR%pids

echo ==============================================
echo   AI Employee System - Stopping...
echo ==============================================
echo.

REM Stop each script by killing Python processes with matching script names
for %%s in (orchestrator.py gmail_watcher.py whatsapp_watcher.py linkedin_watcher.py hitl_watcher.py) do (
    echo [%%~ns] Stopping...
    taskkill /F /FI "WINDOWTITLE eq python*" /IM python.exe /FI "CMDLINE eq *%%s" 2>nul
    if !errorlevel! equ 0 (
        echo [%%~ns] Stopped
    ) else (
        echo [%%~ns] Not running or already stopped
    )
    REM Clean up PID file
    if exist "%PID_DIR%\%%~ns.pid" del /f "%PID_DIR%\%%~ns.pid"
)

echo.
echo ==============================================
echo   AI Employee System - Stopped
echo ==============================================
echo.
echo   To start again: start_ai_employee.bat
echo.

endlocal
