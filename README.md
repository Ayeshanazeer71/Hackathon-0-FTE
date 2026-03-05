# 🤖 AI Employee System - Complete Documentation

A comprehensive autonomous AI employee system that handles email, social media, CRM, invoicing, and business intelligence with full audit logging and error recovery.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Tier Progression](#tier-progression)
3. [Directory Structure](#directory-structure)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [API Keys & Tokens](#api-keys--tokens)
7. [Running the System](#running-the-system)
8. [MCP Servers](#mcp-servers)
9. [Skills Documentation](#skills-documentation)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

The AI Employee System is built in **three tiers**, each adding more capabilities:

| Tier | Capabilities | Status |
|------|-------------|--------|
| **Bronze** | File monitoring, inbox processing, basic orchestration | ✅ Foundation |
| **Silver** | Email, WhatsApp, LinkedIn, HITL approval workflow | ✅ Communication |
| **Gold** | Odoo CRM, Social Media, Twitter, CEO Briefings, Error Recovery, Audit Logging | ✅ Full Automation |

---

## 🏗️ Tier Progression

### BRONZE TIER - Foundation

**Purpose:** Basic file system monitoring and task orchestration

**Components:**
- `filesystem_watcher.py` - Monitors file changes
- `orchestrator.py` - Triggers Claude on new files
- `Dashboard.md` - System status display
- `Company_Handbook.md` - Operating procedures

**Folders Created:**
```
Inbox/           # New files arrive here
Needs_Action/    # Files requiring processing
Plans/           # Generated action plans
Done/            # Completed tasks
Logs/            # System logs
```

**Setup:**
```bash
# No external dependencies required
python filesystem_watcher.py
```

---

### SILVER TIER - Communication

**Purpose:** Multi-channel communication and human-in-the-loop approvals

**New Components:**
- `email_mcp_server.js` - Gmail integration
- `whatsapp_watcher.py` - WhatsApp messaging
- `linkedin_watcher.py` - LinkedIn posts and messages
- `hitl_watcher.py` - Human approval workflow
- `start_ai_employee.sh` - System startup script

**New Folders:**
```
Pending_Approval/  # Awaiting human approval
Approved/          # Approved for execution
Rejected/          # Rejected items
Drafts/            # Email drafts
```

**Setup:**
```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Configure environment variables (see Configuration section)
cp .env.example .env
# Edit .env with your API keys

# Start the system
./start_ai_employee.sh
```

---

### GOLD TIER - Full Automation

**Purpose:** Complete business automation with CRM, social media, and executive reporting

**New Components:**

| File | Purpose |
|------|---------|
| `odoo_mcp_server.js` | Odoo CRM/ERP integration (5 tools) |
| `social_media_watcher.py` | Facebook & Instagram posting |
| `twitter_watcher.py` | Twitter/X with mention monitoring |
| `social_mcp_server.js` | Unified social media MCP server |
| `logging_mcp_server.js` | Centralized logging server |
| `ralph_wiggum.py` | Autonomous loop until task completion |
| `ceo_briefing_generator.py` | Weekly executive briefings |
| `retry_handler.py` | Exponential backoff retry decorator |
| `health_monitor.py` | Process monitoring & auto-restart |
| `degradation_rules.py` | Graceful failure handling |
| `audit_logger.py` | Central audit logging |
| `log_viewer.py` | Log inspection CLI tool |

**New Folders:**
```
Briefings/         # CEO briefings
Accounting/        # Financial data & caches
ralph_state/       # Ralph Wiggum state
Agent_Skills/      # Skill documentation
pids/              # Process ID files
```

**Setup:**
```bash
# Install additional dependencies
pip install tweepy schedule requests

# Configure Odoo (optional)
docker-compose up -d

# Update mcp_config.json with all 4 MCP servers

# Start full system
./start_ai_employee.sh
```

---

## 📁 Complete Directory Structure

```
AI_Employee/
├── 📂 Core System
│   ├── orchestrator.py           # Main orchestrator
│   ├── filesystem_watcher.py     # File monitoring
│   ├── start_ai_employee.sh      # Start all services
│   ├── stop_ai_employee.sh       # Stop all services
│   ├── status_ai_employee.sh     # Check status
│   └── dashboard.md              # System dashboard
│
├── 📂 Communication (Silver)
│   ├── email_mcp_server.js       # Gmail MCP server
│   ├── whatsapp_watcher.py       # WhatsApp monitoring
│   ├── linkedin_watcher.py       # LinkedIn automation
│   └── hitl_watcher.py           # Human-in-the-loop
│
├── 📂 Business Automation (Gold)
│   ├── odoo_mcp_server.js        # Odoo CRM/ERP
│   ├── social_media_watcher.py   # Facebook/Instagram
│   ├── twitter_watcher.py        # Twitter/X
│   ├── social_mcp_server.js      # Social MCP server
│   ├── logging_mcp_server.js     # Logging MCP server
│   └── ceo_briefing_generator.py # Weekly briefings
│
├── 📂 Error Recovery (Gold)
│   ├── retry_handler.py          # Retry decorator
│   ├── health_monitor.py         # Process monitoring
│   └── degradation_rules.py      # Failure handling
│
├── 📂 Audit System (Gold)
│   ├── audit_logger.py           # Central logging
│   └── log_viewer.py             # Log CLI tool
│
├── 📂 Autonomous Loops (Gold)
│   └── ralph_wiggum.py           # Loop until complete
│
├── 📂 Data Folders
│   ├── Inbox/                    # New files arrive here
│   │   ├── social_posts/         # Social media content
│   │   ├── tweets/               # Twitter content
│   │   └── linkedin_posts/       # LinkedIn content
│   ├── Needs_Action/             # Files to process
│   ├── Plans/                    # Generated plans
│   ├── Done/                     # Completed tasks
│   ├── Pending_Approval/         # Awaiting approval
│   ├── Approved/                 # Approved items
│   ├── Rejected/                 # Rejected items
│   ├── Drafts/
│   │   └── queued/               # Queued emails
│   ├── Briefings/                # CEO briefings
│   ├── Accounting/
│   │   ├── Current_Month.md      # Monthly data
│   │   ├── odoo_cache.json       # Odoo cache
│   │   └── flagged_expenses.md   # Expense flags
│   ├── Logs/                     # All logs
│   │   ├── YYYY-MM-DD.json       # Daily audit logs
│   │   ├── health_log.json       # Health monitoring
│   │   ├── errors.json           # Error log
│   │   ├── briefing_log.json     # Briefing history
│   │   ├── ralph_log.json        # Ralph Wiggum logs
│   │   └── failed_tasks/         # Failed task history
│   ├── ralph_state/              # Ralph Wiggum state
│   │   ├── current_task.json
│   │   └── iteration_history.json
│   ├── pids/                     # Process IDs
│   └── Agent_Skills/             # Documentation
│       ├── process_inbox_skill.md
│       ├── linkedin_post_skill.md
│       ├── ralph_wiggum_skill.md
│       ├── ceo_briefing_skill.md
│       └── audit_log_skill.md
│
├── 📂 Configuration
│   ├── .env                      # Environment variables
│   ├── mcp_config.json           # MCP server config
│   ├── docker-compose.yml        # Odoo Docker setup
│   ├── crontab.txt               # Scheduled tasks
│   └── package.json              # Node dependencies
│
└── 📂 Documentation
    ├── README.md                 # This file
    ├── Company_Handbook.md       # Operating procedures
    ├── ODOO_SETUP_GUIDE.md       # Odoo setup
    ├── ODOO_RUNNING.md           # Odoo operations
    └── ODOO_INVOICE_GUIDE.md     # Invoicing guide
```

---

## 🚀 Installation

### Step 1: Clone/Setup Repository

```bash
cd "C:\Users\dell\Desktop\New folder"
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt includes:**
```
requests
tweepy
schedule
pathlib
```

### Step 3: Install Node.js Dependencies

```bash
npm install
```

**Required packages:**
```json
{
  "@modelcontextprotocol/sdk": "^1.27.1",
  "zod": "^3.x",
  "zod-to-json-schema": "^3.x",
  "dotenv": "^17.3.1",
  "nodemailer": "^8.0.1"
}
```

### Step 4: Install Claude CLI (for Ralph Wiggum & CEO Briefing)

```bash
npm install -g @anthropic-ai/claude-code
```

### Step 5: Install Docker (for Odoo)

Download from: https://www.docker.com/products/docker-desktop

---

## 🔐 Configuration

### Environment Variables (.env)

Create a `.env` file in the root directory:

```bash
# ===========================================
# GMAIL CONFIGURATION
# ===========================================
GMAIL_USER=your.email@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password

# ===========================================
# ODOO CONFIGURATION
# ===========================================
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee_db
ODOO_USERNAME=admin
ODOO_PASSWORD=changeme123

# ===========================================
# META (FACEBOOK/INSTAGRAM) CONFIGURATION
# ===========================================
META_ACCESS_TOKEN=your_meta_access_token
META_PAGE_ID=your_facebook_page_id
INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id

# ===========================================
# TWITTER/X CONFIGURATION
# ===========================================
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
```

### How to Get API Keys

#### Gmail App Password
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and your device
5. Copy the 16-character password

#### Meta (Facebook/Instagram) Tokens
1. Go to https://developers.facebook.com/apps
2. Create a new app or select existing
3. Add "Instagram Graph API" product
4. Generate Access Token with permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
5. Get Page ID from Facebook Page About section
6. Get Instagram Account ID via Graph API Explorer

#### Twitter API Keys
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a new project/app
3. Get API Key and Secret from Keys & Tokens
4. Generate Access Token and Secret
5. Get Bearer Token for API v2 access

---

## 🏃 Running the System

### Start All Services

**Windows:**
```batch
start_ai_employee.bat
```

**Linux/Mac:**
```bash
./start_ai_employee.sh
```

### Check Status

```bash
./status_ai_employee.sh
```

### Stop All Services

```bash
./stop_ai_employee.sh
```

### Start Individual Components

```bash
# File system watcher
python filesystem_watcher.py

# Health monitor (Gold tier)
python health_monitor.py

# Social media watcher
python social_media_watcher.py watch

# Twitter watcher
python twitter_watcher.py watch

# CEO Briefing (manual)
python ceo_briefing_generator.py

# Ralph Wiggum (manual)
python ralph_wiggum.py --prompt "Your task" --promise "TASK_COMPLETE"
```

### MCP Servers

MCP servers run automatically when Claude connects via the MCP configuration.

**Manual start (for testing):**
```bash
node email_mcp_server.js
node odoo_mcp_server.js
node social_mcp_server.js
node logging_mcp_server.js
```

---

## 🔌 MCP Servers

The system includes **4 MCP Servers** for Claude integration:

### 1. Email MCP Server (`email`)

**Tools:**
- `send_email` - Send emails via Gmail
- `read_emails` - Read Gmail inbox
- `create_draft` - Create email drafts

**Configuration in mcp_config.json:**
```json
{
  "email": {
    "command": "node",
    "args": ["email_mcp_server.js"],
    "cwd": ".",
    "env": {
      "GMAIL_USER": "your.email@gmail.com",
      "GMAIL_APP_PASSWORD": "your-app-password"
    }
  }
}
```

### 2. Odoo MCP Server (`odoo`)

**Tools:**
- `odoo_get_invoices` - List invoices
- `odoo_create_invoice` - Create draft invoice
- `odoo_get_customers` - Search customers
- `odoo_get_revenue_summary` - Revenue report
- `odoo_flag_expense` - Flag expense for review

**Configuration:**
```json
{
  "odoo": {
    "command": "node",
    "args": ["odoo_mcp_server.js"],
    "env": {
      "ODOO_URL": "http://localhost:8069",
      "ODOO_DB": "ai_employee_db",
      "ODOO_USERNAME": "admin",
      "ODOO_PASSWORD": "changeme123"
    }
  }
}
```

### 3. Social MCP Server (`social`)

**Tools:**
- `post_facebook` - Post to Facebook
- `post_instagram` - Post to Instagram
- `post_tweet` - Post to Twitter
- `get_social_summary` - Combined social report

**Configuration:**
```json
{
  "social": {
    "command": "node",
    "args": ["social_mcp_server.js"],
    "env": {
      "META_ACCESS_TOKEN": "your_token",
      "META_PAGE_ID": "your_page_id",
      "INSTAGRAM_ACCOUNT_ID": "your_ig_id",
      "TWITTER_API_KEY": "your_key",
      "TWITTER_API_SECRET": "your_secret",
      "TWITTER_ACCESS_TOKEN": "your_token",
      "TWITTER_ACCESS_SECRET": "your_secret",
      "TWITTER_BEARER_TOKEN": "your_bearer"
    }
  }
}
```

### 4. Logging MCP Server (`logging`)

**Tools:**
- `write_log` - Write audit log entry
- `read_logs` - Query logs by date range
- `get_audit_summary` - Weekly audit summary

**Configuration:**
```json
{
  "logging": {
    "command": "node",
    "args": ["logging_mcp_server.js"],
    "env": {}
  }
}
```

---

## 📚 Skills Documentation

### Process Inbox Skill (`process_inbox_skill.md`)
How to process files from Inbox → Needs_Action → Plans → Done

### LinkedIn Post Skill (`linkedin_post_skill.md`)
Creating and scheduling LinkedIn posts with approval workflow

### Ralph Wiggum Skill (`ralph_wiggum_skill.md`)
Using autonomous loops for complex multi-step tasks

### CEO Briefing Skill (`ceo_briefing_skill.md`)
Generating weekly executive briefings

### Audit Log Skill (`audit_log_skill.md`)
Understanding and querying the audit log system

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Module not found" errors

```bash
# Python
pip install -r requirements.txt

# Node.js
npm install
```

#### 2. Gmail Authentication Failed

- Ensure 2FA is enabled on Google account
- Use App Password, not regular password
- Check GMAIL_USER is full email address

#### 3. Odoo Connection Refused

```bash
# Check if Odoo is running
docker ps | grep odoo

# Start Odoo
docker-compose up -d

# Check logs
docker-compose logs odoo
```

#### 4. Health Monitor Alerts

```bash
# Check health logs
cat Logs/health_log.json

# Manually restart a service
python orchestrator.py

# Check PID files
ls -la pids/
```

#### 5. Audit Logs Not Appearing

```bash
# Check if audit_logger is imported
grep "from audit_logger" *.py

# Add to each watcher script:
from audit_logger import log_action, log_error, log_system_event
```

#### 6. Claude CLI Not Found

```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### Log Inspection

```bash
# View today's logs
python log_viewer.py --today

# View specific date
python log_viewer.py --date 2026-03-06

# View errors only
python log_viewer.py --errors

# Weekly summary
python log_viewer.py --week

# Filter by action type
python log_viewer.py --actions email_send
```

### Health Check

```bash
# Run health check manually
python health_monitor.py --once

# Check process status
./status_ai_employee.sh
```

---

## 📊 Scheduled Tasks

### Crontab (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add from `crontab.txt`:
```
# CEO Briefing - Every Sunday at 9 PM
0 21 * * 0 cd /path/to/project && python3 ceo_briefing_generator.py

# Social Media - Every 30 minutes
*/30 * * * * cd /path/to/project && python3 social_media_watcher.py process

# Twitter Mentions - Every hour
0 * * * * cd /path/to/project && python3 twitter_watcher.py mentions

# Health Check - Daily at 8 AM
0 8 * * * cd /path/to/project && python3 orchestrator.py health
```

### Windows Task Scheduler

Run the setup script:
```batch
setup_windows_tasks.bat
```

Or manually create tasks in Task Scheduler with the same schedule.

---

## 🔒 Security Best Practices

1. **Never commit .env file** - It's in .gitignore
2. **Rotate API keys regularly** - Especially after staff changes
3. **Use app-specific passwords** - Never use main account passwords
4. **Limit file permissions** - Scripts should be executable only by authorized users
5. **Review audit logs weekly** - Check for unusual activity

---

## 📈 System Monitoring

### Dashboard

View `Dashboard.md` for real-time status:
- Active processes
- Recent completions
- Pending approvals
- System alerts

### Health Monitor

Automatically monitors 9 processes:
- orchestrator.py
- gmail_watcher.py
- whatsapp_watcher.py
- linkedin_watcher.py
- twitter_watcher.py
- social_media_watcher.py
- hitl_watcher.py
- email_mcp_server.js
- odoo_mcp_server.js

Auto-restarts failed processes (max 3 attempts) before alerting.

### Audit Trail

All actions logged to `Logs/YYYY-MM-DD.json`:
- Who performed the action
- What action was taken
- Approval status
- Result (success/failure)

---

## 🎓 Next Steps

1. **Complete Bronze Tier**
   - [ ] Review Company_Handbook.md
   - [ ] Test filesystem_watcher.py
   - [ ] Create first task in Inbox/

2. **Upgrade to Silver Tier**
   - [ ] Configure Gmail API
   - [ ] Test email_mcp_server.js
   - [ ] Set up WhatsApp Business API
   - [ ] Configure LinkedIn API

3. **Upgrade to Gold Tier**
   - [ ] Deploy Odoo via Docker
   - [ ] Configure Meta Business API
   - [ ] Set up Twitter API v2
   - [ ] Test all MCP servers
   - [ ] Schedule CEO briefings

4. **Ongoing Maintenance**
   - [ ] Review audit logs weekly
   - [ ] Update API keys quarterly
   - [ ] Archive old logs monthly
   - [ ] Review and optimize monthly

---

## 📞 Support

For issues or questions:
1. Check Logs/ directory for error details
2. Review Company_Handbook.md for procedures
3. Run `python log_viewer.py --errors` for recent errors
4. Check health status with `./status_ai_employee.sh`

---

**Version:** 1.0.0  
**Last Updated:** 2026-03-06  
**Status:** Gold Tier Complete ✅
