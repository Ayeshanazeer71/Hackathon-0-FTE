# 🧾 Odoo 19 Invoicing - Complete Setup Guide

## 📋 Table of Contents

1. [Odoo Access](#1-odoo-access)
2. [Database Setup](#2-database-setup)
3. [Install Invoicing App](#3-install-invoicing-app)
4. [Create Customer](#4-create-customer)
5. [Create Invoice](#5-create-invoice)
6. [Print Invoice](#6-print-invoice)
7. [Record Payment](#7-record-payment)
8. [Quick Reference](#8-quick-reference)

---

## 1. Odoo Access

### Open Odoo in Browser

```
http://localhost:8069
```

---

## 2. Database Setup

### Step 1: Create Database

When you first open Odoo, you'll see the database creation page:

| Field | Value to Enter |
|-------|----------------|
| **Master Password** | `changeme123` |
| **Database Name** | `ai_employee_db` |
| **Email** | Your email (e.g., `ma9400667@gmail.com`) |
| **Password** | Create a strong password (remember this!) |
| **Language** | English (US) |
| **Country** | Pakistan |
| **Demo Data** | ✅ **Check this box** |

Click **"Create Database"**

### Step 2: Login

After database creation, you'll be redirected to login page:

| Field | Value |
|-------|-------|
| **Email** | The email you entered above |
| **Password** | The password you created above |

---

## 3. Install Invoicing App

### Step 1: Open Apps Menu

1. Click **"Apps"** in top navigation bar (🧩 puzzle piece icon)

### Step 2: Remove Filter

1. Below search box, you'll see **"Apps"** filter
2. Click **"X"** to remove the filter (so all modules show)

### Step 3: Search Invoicing

1. In search box, type: `Invoicing`
2. **"Invoicing"** module will appear (by Odoo S.A.)

### Step 4: Install

1. Click **"Install"** button
2. Wait 20-30 seconds for installation
3. Click **"Open"** button

> ⚠️ **Note:** If you see "Push Notification" error, simply close it. It won't affect Invoicing.

---

## 4. Create Customer

### Step 1: Go to Customers

1. In left sidebar, click **"Customers"**

### Step 2: Create New Customer

1. Click **"Create"** button (top left)

### Step 3: Fill Customer Form

| Field | Example Value |
|-------|---------------|
| **Company Name** | `Test Client A` |
| **Email** | `contact@testclienta.com` |
| **Phone** | `+92-300-1234567` |
| **Address** | `123 Main Street, Karachi` |
| **Website** | (optional) |
| **Tax ID** | (optional) |

### Step 4: Save

1. Click **"Save"** button (💾 floppy disk icon, top left)
2. Customer is created!

---

## 5. Create Invoice

### Step 1: Go to Invoices

1. In left sidebar, click **"Invoices"**

### Step 2: Create New Invoice

1. Click **"Create"** button (top left)
2. Blank invoice form will open

### Step 3: Select Customer

1. Click **"Customer"** field
2. Select **"Test Client A"** from dropdown
3. Address will auto-fill

### Step 4: Add Invoice Lines

In **"Invoice Lines"** table, fill these fields:

| Column | Value | Example |
|--------|-------|---------|
| **Product** | (skip) | Leave blank |
| **Label** | Service name | `Consulting Services` |
| **Quantity** | How many | `1` |
| **Unit Price** | Price per unit | `500` |
| **Taxes** | (optional) | `15%` if applicable |

**Example Entry:**
```
Label:      Consulting Services
Quantity:   1
Unit Price: 500
Taxes:      (blank)
─────────────────────────
Subtotal:   500
```

### Step 5: Add Multiple Lines (Optional)

To add more services:

1. Click **"Add a line"**
2. Fill in additional services:

```
Line 1:
  Label:      Web Development
  Quantity:   5
  Unit Price: 80
  Subtotal:   400

Line 2:
  Label:      Design Services
  Quantity:   2
  Unit Price: 50
  Subtotal:   100

─────────────────────────
Total:        500
```

### Step 6: Save Invoice

1. Click **"Save"** button (top left)
2. Invoice is saved as **"Draft"** (yellow status)

### Step 7: Confirm Invoice

1. Click **"Confirm"** button (top bar)
2. Status changes: **Draft** → **Posted**
3. Color changes: **Yellow** → **Red**
4. **Invoice Number** is assigned (e.g., `INV/2026/0001`)

---

## 6. Print Invoice

### Step 1: Click Print

1. In top bar, click **"Print"** button

### Step 2: Select Format

1. From dropdown, select **"Invoices"**

### Step 3: Download PDF

1. PDF will download automatically
2. Open and review the invoice

---

## 7. Record Payment

### Step 1: Register Payment

1. On the invoice, click **"Register Payment"** button

### Step 2: Fill Payment Form

| Field | Value |
|-------|-------|
| **Amount** | `500` (auto-filled) |
| **Payment Method** | `Bank` or `Cash` |
| **Payment Date** | Today's date |
| **Memo** | `Payment received` |

### Step 3: Create Payment

1. Click **"Create Payment"** button
2. Invoice status: **Posted** → **In Payment** → **Paid**
3. Color changes: **Red** → **Orange** → **Green**

---

## 8. Quick Reference

### Invoice Status Colors

| Color | Status | Meaning |
|-------|--------|---------|
| 🟡 **Yellow** | Draft | Not confirmed yet |
| 🔴 **Red** | Posted | Confirmed, payment pending |
| 🟠 **Orange** | In Payment | Payment processing |
| 🟢 **Green** | Paid | Payment complete |

### Navigation Menu

| Task | Where to Go |
|------|-------------|
| Create Customer | Customers → Create |
| View Customers | Customers |
| Create Invoice | Invoices → Create |
| View Invoices | Invoices |
| Print Invoice | Open Invoice → Print |
| Record Payment | Open Invoice → Register Payment |
| View Reports | Reporting → Invoices Analysis |
| Add Products | Products → Create |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + S` | Save |
| `F5` | Refresh page |
| `Esc` | Close dialog |

### Common Invoice Labels

Use these as examples for your services:

```
- Consulting Services
- Web Development
- Design Services
- Software License
- Support & Maintenance
- Training Services
- Installation Charges
```

---

## 🐛 Troubleshooting

### Issue: Can't access http://localhost:8069

**Solution:**
```bash
# Check if containers are running
docker compose ps

# Restart if needed
docker compose restart
```

### Issue: Invoicing app not showing

**Solution:**
1. Go to Apps
2. Remove "Apps" filter (click X)
3. Search for "Invoicing" again

### Issue: Database already exists error

**Solution:**
1. Go to: `http://localhost:8069/web/database/manager`
2. Enter Master Password: `changeme123`
3. Delete existing database
4. Create new one

### Issue: Push notification error

**Solution:** Simply close the error message. It won't affect Invoicing functionality.

---

## 📊 Sample Invoice Template

```
═══════════════════════════════════════════════════
                    INVOICE
═══════════════════════════════════════════════════

Invoice No:    INV/2026/0001
Date:          March 4, 2026
Due Date:      April 3, 2026

───────────────────────────────────────────────────
BILL TO:
Test Client A
123 Main Street, Karachi
Email: contact@testclienta.com
Phone: +92-300-1234567
───────────────────────────────────────────────────

DESCRIPTION              QTY    UNIT PRICE    AMOUNT
───────────────────────────────────────────────────
Consulting Services       1        500.00      500.00
───────────────────────────────────────────────────

                              Subtotal:         500.00
                              Tax (0%):           0.00
                              ─────────────────────────
                              TOTAL:            500.00
                              ════════════════════════

Payment Terms: Due within 30 days
Thank you for your business!
═══════════════════════════════════════════════════
```

---

## ✅ Setup Checklist

- [ ] Odoo database created
- [ ] Logged in successfully
- [ ] Invoicing app installed
- [ ] Test customer created (Test Client A)
- [ ] Test invoice created ($500)
- [ ] Invoice confirmed (Posted)
- [ ] Invoice printed (PDF)
- [ ] Payment recorded (Paid)

---

## 🔗 Useful Links

| Resource | URL |
|----------|-----|
| Odoo Web Interface | http://localhost:8069 |
| Database Manager | http://localhost:8069/web/database/manager |
| Odoo Documentation | https://www.odoo.com/documentation/19.0/ |
| Odoo Community Forum | https://www.odoo.com/forum/help-1 |

---

## 📞 Support Commands

```bash
# View Odoo logs
docker compose logs odoo --tail 50

# Stop Odoo
docker compose down

# Restart Odoo
docker compose restart

# Remove all data (WARNING!)
docker compose down -v
```

---

**Guide Created:** March 4, 2026  
**Odoo Version:** 19.0 Community Edition  
**Status:** ✅ Running on http://localhost:8069
