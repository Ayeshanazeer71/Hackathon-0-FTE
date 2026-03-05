@echo off
REM Create Daily Briefing File (Windows Batch)
REM Called by Task Scheduler at 8:00 AM daily

set SCRIPT_DIR=%~dp0
set NEEDS_ACTION_DIR=%SCRIPT_DIR%Needs_Action

REM Get current date in YYYY-MM-DD format
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATE=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%
set TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%T%datetime:~8,2%:%datetime:~10,2%:%datetime:~12,2%

set BRIEFING_FILE=%NEEDS_ACTION_DIR%\DAILY_BRIEFING_%DATE%.md

echo Creating daily briefing: %BRIEFING_FILE%

(
echo ---
echo type: daily_briefing
echo created: %TIMESTAMP%
echo priority: high
echo status: pending
echo ---
echo.
echo # Daily Briefing - %DATE%
echo.
echo ## Morning Tasks
echo - [ ] Review overnight emails
echo - [ ] Check pending approvals in Pending_Approval/
echo - [ ] Review any flagged messages from WhatsApp
echo - [ ] Check LinkedIn engagement from previous posts
echo.
echo ## Scheduled Actions
echo - [ ] Review payment logs in Logs/
echo - [ ] Process any items in Approved/ folder
echo - [ ] Update team on progress
echo.
echo ## Notes
echo _Add notes here throughout the day_
echo.
echo ---
echo *Created automatically by AI Employee System*
) > "%BRIEFING_FILE%"

echo Daily briefing created: %BRIEFING_FILE%
