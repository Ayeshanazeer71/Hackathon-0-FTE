@echo off
REM Start AI Employee System (Windows Batch)
REM Starts all watcher scripts as background processes

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PID_DIR=%SCRIPT_DIR%pids
set LOG_DIR=%SCRIPT_DIR%logs

echo ==============================================
echo   AI Employee System - Starting...
echo ==============================================
echo.

REM Create directories
if not exist "%PID_DIR%" mkdir "%PID_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Function to start a script
:start_script
set name=%1
set script=%2
set pid_file=%PID_DIR%\%name%.pid
set log_file=%LOG_DIR%\%name%.log

REM Check if script exists
if not exist "%SCRIPT_DIR%%script%" (
    echo [%name%] Script not found: %script%
    goto :eof
)

REM Check if already running
if exist "%pid_file%" (
    set /p old_pid=<"%pid_file%"
    tasklist /FI "PID eq !old_pid!" 2>nul | findstr "!old_pid!" >nul
    if !errorlevel! equ 0 (
        echo [%name%] Already running (PID: !old_pid!)
        goto :eof
    ) else (
        del /f "%pid_file%"
    )
)

REM Start the script
echo [%name%] Starting...
start /B python "%SCRIPT_DIR%%script%" > "%log_file%" 2>&1
set pid=!errorlevel!

REM Save PID (using a simple approach - store process name)
echo %script% > "%pid_file%"
echo [%name%] Started (logged to %log_file%)
goto :eof

REM Start all scripts
echo Starting watcher scripts...
echo.

call :start_script "orchestrator" "orchestrator.py"
call :start_script "gmail_watcher" "gmail_watcher.py"
call :start_script "whatsapp_watcher" "whatsapp_watcher.py"
call :start_script "linkedin_watcher" "linkedin_watcher.py"
call :start_script "hitl_watcher" "hitl_watcher.py"

echo.
echo ==============================================
echo   AI Employee System - Started
echo ==============================================
echo.
echo   Logs: %LOG_DIR%
echo   PIDs: %PID_DIR%
echo.
echo   To check status: status_ai_employee.bat
echo   To stop all:     stop_ai_employee.bat
echo.

endlocal
