# Odoo 19 Community Edition - Complete Setup Guide

## 📁 Files Created

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Docker configuration for Odoo + PostgreSQL |
| `.env_odoo` | Environment variables template (rename to `.env`) |
| `setup_odoo.sh` | Setup script for Linux/Mac |
| `setup_odoo.bat` | Setup script for Windows |
| `ODOO_SETUP_GUIDE.md` | This guide |

## ⚠️ IMPORTANT: Secure Your Credentials

1. **Rename the environment file:**
   ```bash
   # Linux/Mac
   mv .env_odoo .env
   
   # Windows (PowerShell)
   Move-Item .env_odoo .env
   ```

2. **Edit `.env` and change passwords:**
   ```env
   ODOO_ADMIN_PASSWORD=your_secure_password_here
   POSTGRES_PASSWORD=your_secure_db_password_here
   ```

3. **Add to `.gitignore` immediately:**
   ```bash
   echo ".env" >> .gitignore
   ```

---

## 🚀 Quick Start

### Windows

```bash
# Run the setup script
.\setup_odoo.bat

# Or manually:
docker compose up -d
```

### Linux/Mac

```bash
# Make script executable
chmod +x setup_odoo.sh

# Run setup
./setup_odoo.sh

# Or manually:
docker compose up -d
```

---

## 📋 Step-by-Step Odoo First-Time Setup

### Step 1: Access Odoo Web Interface

Open your browser and go to:
```
http://localhost:8069
```

You'll see the Odoo database creation page.

---

### Step 2: Create Master Database

Fill in the form:

| Field | Value |
|-------|-------|
| **Master Password** | `changeme123` (or your `ODOO_ADMIN_PASSWORD`) |
| **Database Name** | `ai_employee_db` |
| **Email** | Your admin email (e.g., `admin@company.com`) |
| **Password** | Create a secure password (you'll use this to login) |
| **Language** | English (US) |
| **Country** | Your country |
| **Demo Data** | ✅ Check this box (recommended for learning) |

Click **"Create Database"**.

---

### Step 3: Wait for Installation

- Odoo will install the base application (~1-2 minutes)
- You'll see a progress screen
- Automatically redirects to login page when ready

---

### Step 4: Login

| Field | Value |
|-------|-------|
| **Email** | The email you entered in Step 2 |
| **Password** | The password you created in Step 2 |

---

### Step 5: Enable Invoicing & Accounting Modules

After logging in:

1. **Click on "Apps"** (top navigation bar)

2. **Remove "Apps" filter:**
   - Click the filter dropdown next to search
   - Uncheck "Apps" to show all modules

3. **Install Invoicing:**
   - Search for: `Invoicing`
   - Click **"Install"** on the Invoicing module
   - Wait for installation (~30 seconds)

4. **Install Accounting (Community alternative):**
   - Odoo 19 Community doesn't include full Accounting
   - Instead, install: **`Invoicing`** (already done)
   - For full accounting, consider third-party modules from Odoo Apps Store

5. **Optional - Install more modules:**
   - Search and install as needed:
     - `Contacts` - Customer/vendor management
     - `Sales` - Sales orders
     - `Purchase` - Purchase orders
     - `Inventory` - Stock management

---

## 📝 Create Test Customer

1. **Go to Invoicing App** (from main dashboard)

2. **Click on "Customers"** menu (left sidebar)

3. **Click "Create"** button

4. **Fill in customer details:**
   ```
   Company Name: Test Client A
   Contact Name: John Doe (optional)
   Email: contact@testclienta.com
   Phone: +1-555-0123
   Address: 123 Test Street, Test City, TC 12345
   ```

5. **Click "Save"** (top left)

---

## 📄 Create Test Invoice ($500)

1. **Go to Invoicing App**

2. **Click "Customers"** → Select **"Test Client A"**

3. **Click "Create Invoice"** button

4. **Fill in invoice details:**
   
   **Header:**
   ```
   Invoice Type: Customer Invoice
   Customer: Test Client A (should be pre-filled)
   Invoice Date: Today's date
   Due Date: 30 days from today
   ```

   **Invoice Lines:**
   | Label | Quantity | Unit Price |
   |-------|----------|------------|
   | Consulting Services | 1 | $500 |
   
   **Or add multiple lines:**
   | Label | Quantity | Unit Price |
   |-------|----------|------------|
   | Web Development | 5 hours | $80 |
   | Design Services | 2 hours | $50 |

5. **Click "Save"** (top left)

6. **Click "Confirm"** (top bar - changes invoice to Posted state)

7. **Invoice is created!** 
   - Invoice Number will be assigned (e.g., `INV/2026/0001`)
   - Status: **Posted**
   - Amount Due: **$500**

---

## 🔧 Managing Odoo

### View Logs
```bash
# All logs
docker compose logs -f

# Odoo only
docker compose logs -f odoo

# Database only
docker compose logs -f db
```

### Stop Odoo
```bash
docker compose down
```

### Restart Odoo
```bash
docker compose restart
```

### Update Odoo
```bash
docker compose pull
docker compose up -d
```

### Reset Everything (WARNING: Deletes all data!)
```bash
docker compose down -v
```

---

## 📊 Access Database Directly

### PostgreSQL Connection Details
```
Host: localhost
Port: 5432
Database: ai_employee_db
Username: odoo
Password: odoo_secure_pass (or your POSTGRES_PASSWORD)
```

### Connect via psql
```bash
docker exec -it odoo19_postgres psql -U odoo -d ai_employee_db
```

---

## 🛡️ Security Checklist

- [ ] Changed `ODOO_ADMIN_PASSWORD` in `.env`
- [ ] Changed `POSTGRES_PASSWORD` in `.env`
- [ ] Added `.env` to `.gitignore`
- [ ] Using strong admin password for Odoo login
- [ ] Not exposing port 8069 to public network without reverse proxy

---

## 🐛 Troubleshooting

### Port 8069 Already in Use
```bash
# Find what's using port 8069
netstat -ano | findstr :8069

# Or change port in docker-compose.yml
ports:
  - "8070:8069"  # Use port 8070 instead
```

### Containers Won't Start
```bash
# Check Docker is running
docker ps

# Check Docker Compose
docker compose version

# View error logs
docker compose logs
```

### Database Creation Fails
```bash
# Stop and remove volumes
docker compose down -v

# Start fresh
docker compose up -d

# Wait 60 seconds and try again
```

### Can't Access http://localhost:8069
```bash
# Check if container is running
docker compose ps

# Check container logs
docker compose logs odoo

# Restart container
docker compose restart odoo
```

---

## 📚 Next Steps

1. **Configure Company Settings:**
   - Go to Settings → Companies
   - Update your company information

2. **Set Up Users:**
   - Go to Settings → Users & Companies → Users
   - Create additional user accounts

3. **Configure Chart of Accounts:**
   - Invoicing → Configuration → Accounting
   - Review and customize accounts

4. **Create Products:**
   - Invoicing → Products → Products
   - Add your services/products

5. **Explore Odoo Apps:**
   - Visit Odoo Apps Store: https://apps.odoo.com/
   - Install additional community modules

---

## 📖 Resources

- **Official Odoo Documentation:** https://www.odoo.com/documentation/19.0/
- **Odoo Community Forum:** https://www.odoo.com/forum/help-1
- **GitHub Issues:** https://github.com/odoo/odoo/issues
- **Docker Image:** https://hub.docker.com/_/odoo

---

## ✅ Setup Confirmation Checklist

- [ ] `docker-compose.yml` created
- [ ] `.env` file configured with secure passwords
- [ ] `.env` added to `.gitignore`
- [ ] Containers running (`docker compose ps`)
- [ ] Can access http://localhost:8069
- [ ] Database created
- [ ] Logged in successfully
- [ ] Invoicing module installed
- [ ] Test customer "Test Client A" created
- [ ] Test invoice for $500 created

---

**Setup Complete!** 🎉

Your Odoo 19 Community Edition is now running locally with Docker.
