# Audit Logging System Skill

## Overview

The Audit Logging System ensures **every single action** taken by the AI Employee is logged in a structured, queryable format. This provides complete traceability for compliance, debugging, and analysis.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIT LOGGING SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  audit_logger.py                                                │
│  ├── log_action()     - Log actions (email_send, payment, etc.) │
│  ├── log_error()      - Log errors with stack traces            │
│  ├── log_system_event() - Log system events (start, stop, etc.) │
│  └── [Query functions]  - Get logs by date, type, actor, etc.   │
│                                                                 │
│  log_viewer.py (CLI)                                            │
│  ├── --date YYYY-MM-DD  - View specific date                    │
│  ├── --week             - Weekly summary                        │
│  ├── --errors           - Show only errors                      │
│  ├── --actions TYPE     - Filter by action type                 │
│  └── --summary          - Statistics                            │
│                                                                 │
│  ./Logs/YYYY-MM-DD.json (Daily log files)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Log Format

Every log entry follows this structure:

```json
{
  "timestamp": "2026-03-05T14:30:22.123456",
  "log_type": "action",
  "action_type": "email_send",
  "actor": "gmail_watcher",
  "target": "user@example.com",
  "parameters": {
    "subject": "Weekly Report",
    "body_preview": "Please find attached..."
  },
  "approval_status": "auto_approved",
  "approved_by": "system",
  "result": "success",
  "error": null
}
```

### Field Definitions

| Field | Description | Values |
|-------|-------------|--------|
| `timestamp` | ISO format timestamp | `2026-03-05T14:30:22` |
| `log_type` | Category of log | `action`, `error`, `system` |
| `action_type` | Specific action performed | `email_send`, `payment`, `social_post`, etc. |
| `actor` | Who performed the action | `gmail_watcher`, `claude`, `hitl_watcher`, etc. |
| `target` | Who/what was affected | Email address, file path, etc. |
| `parameters` | Action details | Varies by action |
| `approval_status` | Approval state | `auto_approved`, `human_approved`, `pending`, `rejected` |
| `approved_by` | Who approved | `human`, `system`, `N/A` |
| `result` | Outcome | `success`, `failed`, `pending` |
| `error` | Error message if failed | String or null |

---

## Usage in Scripts

### Import Statement

Add this to the top of any script that needs logging:

```python
from audit_logger import log_action, log_error, log_system_event
```

### Log an Action

```python
from audit_logger import log_action

# After successfully sending an email
log_action(
    action_type='email_send',
    actor='gmail_watcher',
    target='user@example.com',
    parameters={
        'subject': 'Weekly Report',
        'attachments': ['report.pdf']
    },
    result='success',
    approval_status='auto_approved',
    approved_by='system'
)
```

### Log an Error

```python
from audit_logger import log_error
import traceback

try:
    send_email(...)
except Exception as e:
    log_error(
        component='gmail_watcher',
        error_type=type(e).__name__,
        error_message=str(e),
        stack_trace=traceback.format_exc(),
        actor='gmail_watcher',
        target='user@example.com'
    )
```

### Log a System Event

```python
from audit_logger import log_system_event

# At script startup
log_system_event(
    event_type='system_start',
    details={
        'version': '1.0.0',
        'pid': os.getpid(),
        'config': 'production'
    }
)
```

### Use Decorator for Automatic Logging

```python
from audit_logger import audit_log

@audit_log('email_send', actor='gmail_watcher')
def send_email(to, subject, body):
    # Automatically logs on success or failure
    ...
```

---

## Integration Guide

### gmail_watcher.py

```python
from audit_logger import log_action, log_error

# When sending email
def send_email(to, subject, body):
    try:
        # ... send email code ...
        log_action(
            action_type='email_send',
            actor='gmail_watcher',
            target=to,
            parameters={'subject': subject},
            result='success',
            approval_status='auto_approved',
            approved_by='system'
        )
    except Exception as e:
        log_error(
            component='gmail_watcher',
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
```

### whatsapp_watcher.py

```python
from audit_logger import log_action, log_error

# When sending WhatsApp message
log_action(
    action_type='whatsapp_send',
    actor='whatsapp_watcher',
    target=phone_number,
    parameters={'message_preview': message[:100]},
    result='success',
    approval_status='auto_approved',
    approved_by='system'
)
```

### linkedin_watcher.py

```python
from audit_logger import log_action, log_error

# When posting to LinkedIn
log_action(
    action_type='linkedin_post',
    actor='linkedin_watcher',
    target='linkedin_company_page',
    parameters={'content_preview': content[:100]},
    result='success',
    approval_status='human_approved',
    approved_by='human'
)
```

### twitter_watcher.py

```python
from audit_logger import log_action, log_error

# When posting tweet
log_action(
    action_type='tweet_post',
    actor='twitter_watcher',
    target='twitter_account',
    parameters={'tweet_text': text},
    result='success',
    approval_status='auto_approved',
    approved_by='system'
)
```

### social_media_watcher.py

```python
from audit_logger import log_action, log_error

# When posting to Facebook/Instagram
log_action(
    action_type='facebook_post',  # or 'instagram_post'
    actor='social_media_watcher',
    target='facebook_page',
    parameters={'content': content[:200]},
    result='success',
    approval_status='human_approved',
    approved_by='human'
)
```

### hitl_watcher.py

```python
from audit_logger import log_action, log_error

# When human approves/rejects
log_action(
    action_type='human_approval',
    actor='hitl_watcher',
    target=file_path,
    parameters={
        'decision': 'approved',
        'reviewer': 'admin'
    },
    result='success',
    approval_status='human_approved',
    approved_by='human'
)
```

### orchestrator.py

```python
from audit_logger import log_action, log_system_event

# At startup
log_system_event('system_start', {'version': '1.0.0'})

# When orchestrating tasks
log_action(
    action_type='task_orchestrate',
    actor='orchestrator',
    target=task_name,
    parameters={'priority': 'high'},
    result='success',
    approval_status='auto_approved',
    approved_by='system'
)
```

### ceo_briefing_generator.py

```python
from audit_logger import log_action, log_system_event

# When generating briefing
log_action(
    action_type='briefing_generate',
    actor='ceo_briefing_generator',
    target='weekly_ceo_briefing',
    parameters={'week': '2026-W10'},
    result='success',
    approval_status='auto_approved',
    approved_by='system'
)
```

---

## Log Viewer CLI

### View Logs for Specific Date

```bash
python log_viewer.py --date 2026-03-05
```

### View This Week's Summary

```bash
python log_viewer.py --week
```

### View Only Errors

```bash
python log_viewer.py --errors
python log_viewer.py --errors --date 2026-03-05  # Specific date
```

### Filter by Action Type

```bash
python log_viewer.py --actions email_send
python log_viewer.py --actions payment --date 2026-03-05
```

### View Today's Logs

```bash
python log_viewer.py --today
python log_viewer.py --today --verbose  # With details
```

### Show Summary Statistics

```bash
python log_viewer.py --summary
python log_viewer.py --summary --date 2026-03-05
```

### Full Options

```
usage: log_viewer.py [-h] [--date DATE] [--week] [--today] [--errors]
                     [--actions ACTIONS] [--type {action,error,system}]
                     [--summary] [--verbose] [--limit LIMIT]

Options:
  --date, -d          Show logs for specific date (YYYY-MM-DD)
  --week, -w          Show summary for the last 7 days
  --today, -t         Show today's logs
  --errors, -e        Show only error logs
  --actions, -a       Filter by action type
  --type              Filter by log type (action, error, system)
  --summary, -s       Show summary statistics
  --verbose, -v       Show verbose output with details
  --limit, -l         Limit entries shown (default: 100)
```

---

## Query Functions (Programmatic Access)

```python
from audit_logger import (
    get_logs_for_date,
    get_logs_by_type,
    get_logs_by_action_type,
    get_errors,
    get_logs_by_actor,
    get_summary
)

# Get all logs for a date
logs = get_logs_for_date('2026-03-05')

# Get only error logs
errors = get_errors()
errors_yesterday = get_errors('2026-03-04')

# Get logs by action type
emails = get_logs_by_action_type('email_send')

# Get logs by actor
gmail_logs = get_logs_by_actor('gmail_watcher')

# Get summary statistics
summary = get_summary()
print(f"Total: {summary['total_logs']}, Errors: {summary['errors']}")
```

---

## Action Types Reference

| Action Type | Description | Typical Actor |
|-------------|-------------|---------------|
| `email_send` | Sending email | gmail_watcher |
| `email_receive` | Receiving email | gmail_watcher |
| `whatsapp_send` | Sending WhatsApp message | whatsapp_watcher |
| `linkedin_post` | LinkedIn post | linkedin_watcher |
| `linkedin_message` | LinkedIn message | linkedin_watcher |
| `tweet_post` | Twitter/X tweet | twitter_watcher |
| `facebook_post` | Facebook post | social_media_watcher |
| `instagram_post` | Instagram post | social_media_watcher |
| `payment_create` | Create payment | odoo_mcp_server |
| `invoice_create` | Create invoice | odoo_mcp_server |
| `invoice_post` | Post invoice | odoo_mcp_server |
| `file_move` | Move file between folders | hitl_watcher |
| `file_process` | Process file content | orchestrator |
| `human_approval` | Human approved/rejected | hitl_watcher |
| `task_orchestrate` | Orchestrate task | orchestrator |
| `briefing_generate` | Generate CEO briefing | ceo_briefing_generator |
| `system_start` | System/component started | Any |
| `system_stop` | System/component stopped | Any |

---

## Approval Status Values

| Status | Description |
|--------|-------------|
| `auto_approved` | System automatically approved (within rules) |
| `human_approved` | Human reviewed and approved |
| `pending` | Awaiting approval |
| `rejected` | Human or system rejected |
| `N/A` | Not applicable (system events) |

---

## Best Practices

1. **Log Early, Log Often** - Every action should be logged
2. **Include Context** - Add relevant parameters for debugging
3. **Log Errors with Stack Traces** - Use `traceback.format_exc()`
4. **Use Consistent Action Types** - Follow the reference table
5. **Set Correct Approval Status** - Distinguish auto vs human approval
6. **Review Logs Regularly** - Use `log_viewer.py --week` for insights

---

## Log Retention

- Logs are stored in `./Logs/YYYY-MM-DD.json` format
- One file per day
- Recommended retention: 90 days (configure log rotation)
- Archive old logs to `./Logs/archive/` for compliance

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Logs not appearing | Check file permissions on ./Logs/ directory |
| JSON parse errors | Corrupted log file - backup and recreate |
| Missing fields | Ensure all required fields are provided |
| Slow logging | Logs are synchronous - consider async for high volume |

---

*Generated for AI Employee System*
*Version: 1.0.0*
