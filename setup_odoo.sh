#!/bin/bash
# =============================================================================
# Odoo 19 Community Edition Setup Script
# =============================================================================
# This script starts Odoo 19 with PostgreSQL using Docker Compose
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}          Odoo 19 Community Edition Setup${NC}"
echo -e "${CYAN}============================================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed. Please install Docker first.${NC}"
    echo -e "${YELLOW}Visit: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not installed.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found!${NC}"
    echo -e "${YELLOW}Creating .env file with default values...${NC}"
    cp .env_odoo .env
    echo -e "${GREEN}Created .env file. Please edit with your secure passwords!${NC}"
fi

# Create required directories
echo -e "${CYAN}[SETUP]${NC} Creating required directories..."
mkdir -p ./odoo/addons
mkdir -p ./odoo/logs

# Start containers
echo -e "${CYAN}[START]${NC} Starting Odoo 19 and PostgreSQL containers..."

# Use docker compose (v2) or docker-compose (v1)
if docker compose version &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi

echo -e "${YELLOW}[WAIT]${NC} Waiting 30 seconds for containers to initialize..."

# Countdown timer
for i in {30..1}; do
    printf "\r${YELLOW}[%02d]${NC} seconds remaining..." "$i"
    sleep 1
done
echo ""

# Check container status
echo -e "${CYAN}[STATUS]${NC} Checking container status..."

if docker compose ps &> /dev/null; then
    docker compose ps
else
    docker-compose ps
fi

# Get Odoo URL
ODOO_URL="http://localhost:8069"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}          Odoo 19 is Running!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "${CYAN}Odoo Web Interface:${NC} ${GREEN}${ODOO_URL}${NC}"
echo ""
echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}     FIRST-TIME SETUP INSTRUCTIONS${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""
echo -e "${CYAN}Step 1:${NC} Open your browser and go to ${GREEN}${ODOO_URL}${NC}"
echo ""
echo -e "${CYAN}Step 2:${NC} Create Master Password"
echo "   - You'll see a database creation page"
echo "   - Master Password: ${GREEN}changeme123${NC} (or your ODOO_ADMIN_PASSWORD)"
echo "   - Click 'Create Database'"
echo ""
echo -e "${CYAN}Step 3:${NC} Fill in Database Details"
echo "   - Database Name: ${GREEN}ai_employee_db${NC}"
echo "   - Email: Enter your admin email"
echo "   - Password: Create your admin password (remember this!)"
echo "   - Language: Select your preferred language"
echo "   - Country: Select your country"
echo "   - Click 'Create Database'"
echo ""
echo -e "${CYAN}Step 4:${NC} Wait for Installation"
echo "   - Odoo will install (takes 1-2 minutes)"
echo "   - You'll be redirected to the login page"
echo ""
echo -e "${CYAN}Step 5:${NC} Login"
echo "   - Email: The email you entered in Step 3"
echo "   - Password: The password you created in Step 3"
echo ""
echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}     POST-INSTALLATION: Enable Modules${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""
echo "After logging in for the first time:"
echo ""
echo -e "${CYAN}1.${NC} Go to ${GREEN}Apps${NC} menu (top navigation)"
echo -e "${CYAN}2.${NC} Search for and install these modules:"
echo "   - ${GREEN}Invoicing${NC} (click Install)"
echo "   - ${GREEN}Accounting${NC} (if available in Community, or use Invoicing)"
echo ""
echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}     Useful Commands${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""
echo "View logs:          docker-compose logs -f odoo"
echo "Stop containers:    docker-compose down"
echo "Restart:            docker-compose restart"
echo "Remove all data:    docker-compose down -v (WARNING: Deletes all data!)"
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}Setup Complete! Access Odoo at ${ODOO_URL}${NC}"
echo -e "${GREEN}============================================================${NC}"
