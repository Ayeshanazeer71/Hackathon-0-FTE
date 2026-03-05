@echo off
REM =============================================================================
REM Odoo 19 Community Edition Setup Script (Windows)
REM =============================================================================
REM This script starts Odoo 19 with PostgreSQL using Docker Compose
REM =============================================================================

setlocal enabledelayedexpansion

echo ============================================================
echo          Odoo 19 Community Edition Setup
echo ============================================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Docker Compose is not installed.
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker-compose
) else (
    set COMPOSE_CMD=docker compose
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Creating .env file with default values...
    copy .env_odoo .env >nul
    echo Created .env file. Please edit with your secure passwords!
)

REM Create required directories
echo [SETUP] Creating required directories...
if not exist "odoo\addons" mkdir odoo\addons
if not exist "odoo\logs" mkdir odoo\logs

REM Start containers
echo [START] Starting Odoo 19 and PostgreSQL containers...
%COMPOSE_CMD% up -d

echo [WAIT] Waiting 30 seconds for containers to initialize...
timeout /t 30 /nobreak >nul

REM Check container status
echo [STATUS] Checking container status...
%COMPOSE_CMD% ps

echo.
echo ============================================================
echo          Odoo 19 is Running!
echo ============================================================
echo.
echo Odoo Web Interface: http://localhost:8069
echo.
echo ============================================================
echo      FIRST-TIME SETUP INSTRUCTIONS
echo ============================================================
echo.
echo Step 1: Open your browser and go to http://localhost:8069
echo.
echo Step 2: Create Master Password
echo    - You'll see a database creation page
echo    - Master Password: changeme123 (or your ODOO_ADMIN_PASSWORD)
echo    - Click 'Create Database'
echo.
echo Step 3: Fill in Database Details
echo    - Database Name: ai_employee_db
echo    - Email: Enter your admin email
echo    - Password: Create your admin password (remember this!)
echo    - Language: Select your preferred language
echo    - Country: Select your country
echo    - Click 'Create Database'
echo.
echo Step 4: Wait for Installation
echo    - Odoo will install (takes 1-2 minutes)
echo    - You'll be redirected to the login page
echo.
echo Step 5: Login
echo    - Email: The email you entered in Step 3
echo    - Password: The password you created in Step 3
echo.
echo ============================================================
echo      POST-INSTALLATION: Enable Modules
echo ============================================================
echo.
echo After logging in for the first time:
echo.
echo 1. Go to Apps menu (top navigation)
echo 2. Search for and install these modules:
echo    - Invoicing (click Install)
echo    - Accounting (if available in Community, or use Invoicing)
echo.
echo ============================================================
echo      Useful Commands
echo ============================================================
echo.
echo View logs:          docker-compose logs -f odoo
echo Stop containers:    docker-compose down
echo Restart:            docker-compose restart
echo Remove all data:    docker-compose down -v (WARNING: Deletes all data!)
echo.
echo ============================================================
echo Setup Complete! Access Odoo at http://localhost:8069
echo ============================================================
echo.
pause
