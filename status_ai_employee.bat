@echo off
REM Check AI Employee System Status (Windows Batch)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PID_DIR=%SCRIPT_DIR%pids

echo ==============================================
echo   AI Employee System - Status Check
echo ==============================================
echo.

set running_count=0
set total_count=5

echo SCRIPT               STATUS
echo ----------------------------------------------

for %%s in (orchestrator gmail_watcher whatsapp_watcher linkedin_watcher hitl_watcher) do (
    set /p pid=<"%PID_DIR%\%%s.pid" 2>nul
    if "!pid!"=="" (
        echo %%s               STOPPED
    ) else (
        tasklist /FI "PID eq !pid!" 2>nul | findstr "!pid!" >nul
        if !errorlevel! equ 0 (
            echo %%s               RUNNING (PID: !pid!)
            set /a running_count+=1
        ) else (
            echo %%s               STOPPED (stale)
        )
    )
)

echo ----------------------------------------------
echo.
echo Summary:
echo   Running:  %running_count% / %total_count%
echo   Stopped:  %total_count - %running_count% / %total_count%
echo.

if %running_count% equ 0 (
    echo No scripts running. Start with:
    echo   start_ai_employee.bat
) else if %running_count% lss %total_count% (
    echo Some scripts not running.
    echo   Restart: stop_ai_employee.bat ^&^& start_ai_employee.bat
) else (
    echo All systems operational!
)

echo.
echo ==============================================
echo.

endlocal
