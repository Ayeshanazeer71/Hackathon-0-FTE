@echo off
REM AI Employee System - Windows Task Scheduler Setup
REM Run this script to create scheduled tasks for Windows

REM ============================================
REM WEEKLY CEO BRIEFING
REM Every Sunday at 9:00 PM
REM ============================================
schtasks /Create /TN "AI_Employee_CEO_Briefing" /TR "python \"%~dp0ceo_briefing_generator.py\"" /SC WEEKLY /D SUN /ST 21:00 /RL LIMITED /F

REM ============================================
REM SOCIAL MEDIA WATCHER
REM Every 30 minutes
REM ============================================
schtasks /Create /TN "AI_Employee_Social_Watcher" /TR "python \"%~dp0social_media_watcher.py\" process" /SC MINUTE /MO 30 /RL LIMITED /F

REM ============================================
REM TWITTER MENTIONS CHECK
REM Every hour
REM ============================================
schtasks /Create /TN "AI_Employee_Twitter_Mentions" /TR "python \"%~dp0twitter_watcher.py\" mentions" /SC HOURLY /RL LIMITED /F

REM ============================================
REM DAILY HEALTH CHECK
REM Every day at 8:00 AM
REM ============================================
schtasks /Create /TN "AI_Employee_Daily_Health" /TR "python \"%~dp0orchestrator.py\" health" /SC DAILY /ST 08:00 /RL LIMITED /F

echo.
echo Scheduled tasks created successfully!
echo.
echo To view tasks: schtasks /Query /TN "AI_Employee*"
echo To delete tasks: schtasks /Delete /TN "AI_Employee_*" /F
echo.
