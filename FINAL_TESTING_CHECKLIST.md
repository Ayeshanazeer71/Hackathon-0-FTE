# 🧪 AI Employee System - Final Testing Checklist

## Pre-Testing Setup

### 1. Check All Services Status
```bash
# Windows
docker compose ps
python --version
node --version

# Verify .env file exists
dir .env
```

---

## ✅ Tier 1: Bronze Tier (Foundation)

### Test 1.1: File System Watcher
- [ ] Start filesystem watcher
- [ ] Create test file in Inbox/
- [ ] Verify file detected
- [ ] Check Logs/ for activity

**Command:**
```bash
python filesystem_watcher.py
```

**Expected:** File changes detected and logged

---

### Test 1.2: Orchestrator
- [ ] Start orchestrator
- [ ] Check Dashboard.md updates
- [ ] Verify process running

**Command:**
```bash
python orchestrator.py
```

---

## ✅ Tier 2: Silver Tier (Communication)

### Test 2.1: Email System
- [ ] Configure Gmail credentials in .env
- [ ] Test email MCP server
- [ ] Send test email
- [ ] Read inbox

**Commands:**
```bash
node email_mcp_server.js
```

**Test:** Send email to yourself

---

### Test 2.2: Twitter (Playwright)
- [ ] ✅ Already tested - WORKING
- [ ] Post another test tweet
- [ ] Verify on twitter.com

**Command:**
```bash
python playwright_twitter_poster.py ai "Testing AI automation"
```

**Expected:** Tweet posted successfully

---

### Test 2.3: LinkedIn
- [ ] Add LinkedIn credentials to .env
- [ ] Generate test post
- [ ] Post to LinkedIn

**Command:**
```bash
python linkedin_watcher.py
```

---

### Test 2.4: Human-in-the-Loop (HITL)
- [ ] Create file in Pending_Approval/
- [ ] Move to Approved/
- [ ] Verify processing

---

## ✅ Tier 3: Gold Tier (Full Automation)

### Test 3.1: Odoo Integration
- [ ] ✅ Already tested - WORKING
- [ ] Create test invoice via API
- [ ] Get customer list
- [ ] Get revenue summary

**Command:**
```bash
node test_odoo_xmlrpc.js
```

**Expected:** 6 customers, 57 invoices found

---

### Test 3.2: Social Media (Facebook/Instagram)
- [ ] Add Meta credentials to .env
- [ ] Test Facebook post
- [ ] Test Instagram post

**Command:**
```bash
python social_media_watcher.py check
```

---

### Test 3.3: CEO Briefing
- [ ] Generate weekly briefing
- [ ] Check Briefings/ folder
- [ ] Verify report content

**Command:**
```bash
python ceo_briefing_generator.py
```

**Expected:** CEO briefing created in Briefings/

---

### Test 3.4: Audit Logging
- [ ] Check Logs/ folder
- [ ] Verify today's log file
- [ ] Check log entries

**Command:**
```bash
python log_viewer.py --today
```

---

### Test 3.5: Health Monitor
- [ ] Start health monitor
- [ ] Verify all processes tracked
- [ ] Check health_log.json

**Command:**
```bash
python health_monitor.py --once
```

---

### Test 3.6: Ralph Wiggum (Autonomous Agent)
- [ ] Test simple task
- [ ] Verify task completion
- [ ] Check ralph_state/

**Command:**
```bash
python ralph_wiggum.py --prompt "Check Odoo invoices" --promise "TASK_COMPLETE"
```

---

## 🔧 Configuration Tests

### Test All MCP Servers

**Email MCP:**
```bash
node email_mcp_server.js
```

**Odoo MCP:**
```bash
node odoo_mcp_server.js
```

**Social MCP:**
```bash
node social_mcp_server.js
```

**Logging MCP:**
```bash
node logging_mcp_server.js
```

---

## 📊 Integration Test: End-to-End Workflow

### Scenario: Invoice from Email

1. **Email arrives** → "Please invoice $1000 for consulting"
2. **AI reads email** → Email MCP
3. **Create invoice** → Odoo MCP
4. **Send confirmation** → Email MCP
5. **Log action** → Audit Logger
6. **Update Dashboard** → Dashboard.md

**Test Steps:**
```bash
# 1. Create email file
echo "Invoice request: $1000 for consulting" > Inbox/test_invoice.txt

# 2. Run orchestrator
python orchestrator.py

# 3. Check Odoo for new invoice
node test_odoo_xmlrpc.js

# 4. Check audit log
python log_viewer.py --today
```

---

## 🎯 Final Verification

### Checklist

- [ ] All Python scripts run without errors
- [ ] All Node.js servers start successfully
- [ ] Twitter posting works ✅
- [ ] Odoo connection works ✅
- [ ] Email sending/receiving works
- [ ] LinkedIn posting works
- [ ] Facebook/Instagram posting works
- [ ] CEO briefing generates
- [ ] Audit logs created
- [ ] Health monitor tracks processes
- [ ] Dashboard updates

---

## 🚀 Deployment Steps

### 1. Start All Services

**Windows:**
```batch
start_ai_employee.bat
```

**Linux/Mac:**
```bash
./start_ai_employee.sh
```

### 2. Verify Running

```bash
./status_ai_employee.sh
```

### 3. Schedule Tasks

**Windows Task Scheduler** or **Linux Cron**

### 4. Monitor First Week

- Check logs daily
- Review audit trail
- Monitor health alerts

---

## 📝 Test Results Template

| Component | Status | Notes |
|-----------|--------|-------|
| File Watcher | ⬜ Pass/Fail | |
| Orchestrator | ⬜ Pass/Fail | |
| Email MCP | ⬜ Pass/Fail | |
| Twitter | ✅ Pass | Working |
| LinkedIn | ⬜ Pass/Fail | |
| Odoo | ✅ Pass | Working |
| Social Media | ⬜ Pass/Fail | |
| CEO Briefing | ⬜ Pass/Fail | |
| Audit Logger | ⬜ Pass/Fail | |
| Health Monitor | ⬜ Pass/Fail | |
| Ralph Wiggum | ⬜ Pass/Fail | |

---

## 🐛 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Module not found | `pip install -r requirements.txt` or `npm install` |
| Authentication failed | Check .env credentials |
| Port already in use | Change port in config |
| Docker not running | `docker compose up -d` |
| API rate limit | Wait and retry |

---

## ✅ Sign-Off

**Tested by:** _______________
**Date:** _______________
**Overall Status:** ⬜ PASS / ⬜ FAIL

**Notes:**
_______________________________________
_______________________________________
