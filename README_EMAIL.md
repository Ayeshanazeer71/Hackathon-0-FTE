# Email MCP Server Setup Guide

Send emails and manage drafts via Gmail with built-in approval workflow.

## Quick Setup (3 Steps)

### 1. Get Gmail App Password

1. **Enable 2-Step Verification** (if not already):
   - Go to: https://myaccount.google.com/security
   - Turn on 2-Step Verification

2. **Generate App Password**:
   - Visit: https://myaccount.google.com/apppasswords
   - Select:
     - **App**: `Mail`
     - **Device**: `Other` → Enter "AI Employee"
   - Click **Generate**
   - Copy the 16-character password (format: `abcd efgh ijkl mnop`)

   ![App Password Example](https://i.imgur.com/example.png)

### 2. Configure .env File

Edit `.env` in the project root:

```bash
# Replace with your actual Gmail credentials
GMAIL_USER=your.email@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
```

**Important**: Remove spaces from the app password if needed:
```bash
GMAIL_APP_PASSWORD=abcdefghijklmnop
```

### 3. Add Approved Contacts

Edit `approved_contacts.txt` and add email addresses (one per line):

```text
# Approved Email Contacts
colleague@company.com
boss@organization.com
team@example.com
```

**Security**: Emails to non-approved contacts are saved as drafts instead of sent.

## Testing Setup

### Test with Node.js directly

```bash
# Start the server (for MCP integration)
node email_mcp_server.js
```

### Verify Configuration

Check if everything is set up correctly:

```bash
# The server will show status on startup:
# Starting Email MCP Server...
# Gmail User: configured  ← Should show "configured"
```

## Available Tools

### 1. `send_email` - Send an Email

Sends email to approved contacts only.

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject
- `body` (required): Email content

**Example:**
```javascript
{
  "name": "send_email",
  "arguments": {
    "to": "colleague@company.com",
    "subject": "Meeting Tomorrow",
    "body": "Hi,\n\nJust a reminder about our meeting tomorrow at 2 PM.\n\nBest regards"
  }
}
```

**Response:**
```
✅ Email sent successfully to colleague@company.com
Subject: Meeting Tomorrow
Timestamp: 2026-03-04T10:30:00.000Z
```

**If recipient not approved:**
```
⚠️ Recipient "unknown@example.com" is not in approved_contacts.txt. 
Email saved as draft instead: Drafts/draft_Meeting_Tomorrow_2026-03-04T10-30-00.md

To send emails to this recipient, add their address to approved_contacts.txt first.
```

### 2. `draft_email` - Save Email Draft

Saves an email draft without sending.

**Parameters:**
- `to`: Recipient email address
- `subject`: Email subject
- `body`: Email content

**Example:**
```javascript
{
  "name": "draft_email",
  "arguments": {
    "to": "someone@example.com",
    "subject": "Draft Proposal",
    "body": "This is a draft..."
  }
}
```

**Response:**
```
📝 Draft saved successfully
File: Drafts/draft_Draft_Proposal_2026-03-04T10-30-00.md
To: someone@example.com
Subject: Draft Proposal
```

### 3. `list_drafts` - List All Drafts

Shows all draft email files.

**Response:**
```
📋 Draft Files (3 total):

1. draft_Meeting_Notes_2026-03-04T10-30-00.md
2. draft_Project_Update_2026-03-04T09-15-00.md
3. draft_Quick_Question_2026-03-03T16-45-00.md
```

## Directory Structure

```
Project Root/
├── Drafts/                    ← Email drafts saved here
│   ├── draft_Meeting_2026-03-04T10-30-00.md
│   └── draft_Proposal_2026-03-04T09-15-00.md
├── Logs/
│   └── email_log.json        ← Activity log
├── approved_contacts.txt      ← Approved recipient list
└── email_mcp_server.js        ← Server script
```

## Draft File Format

Drafts are saved as Markdown with frontmatter:

```markdown
---
type: email_draft
to: colleague@company.com
subject: Meeting Tomorrow
created: 2026-03-04T10:30:00.000Z
status: draft
---

## Email Content

Hi,

Just a reminder about our meeting tomorrow at 2 PM.

Best regards

---
*Draft created by Email MCP Server*
```

## Activity Logging

All email attempts are logged to `Logs/email_log.json`:

```json
[
  {
    "timestamp": "2026-03-04T10:30:00.000Z",
    "to": "colleague@company.com",
    "subject": "Meeting Tomorrow",
    "status": "success",
    "error": null
  },
  {
    "timestamp": "2026-03-04T10:35:00.000Z",
    "to": "unknown@example.com",
    "subject": "Test",
    "status": "saved_as_draft",
    "error": "Recipient not approved"
  }
]
```

Logs are automatically rotated (keeps last 1000 entries).

## Troubleshooting

### "Gmail credentials not configured"

**Problem**: `.env` file missing or credentials not set.

**Solution**:
1. Check `.env` exists in project root
2. Verify `GMAIL_USER` and `GMAIL_APP_PASSWORD` are set
3. Restart the server

### "Invalid email address"

**Problem**: Recipient email format is invalid.

**Solution**: Ensure email contains `@` symbol, e.g., `user@example.com`

### "Recipient not in approved_contacts.txt"

**Problem**: Trying to send to unapproved address.

**Solution** (choose one):
1. Add recipient to `approved_contacts.txt`
2. Use `draft_email` tool instead to save as draft

### "App Password not working"

**Problem**: Wrong password or 2FA not enabled.

**Solution**:
1. Ensure 2-Step Verification is enabled
2. Generate a new app password
3. Make sure you're using the app password, not your regular Gmail password
4. Try removing spaces: `abcd efgh ijkl mnop` → `abcdefghijklmnop`

### "Cannot connect to Gmail SMTP"

**Problem**: Network or firewall issue.

**Solution**:
1. Check internet connection
2. Verify firewall allows outbound connections on port 587
3. Try again in a few minutes

## Security Best Practices

- 🔐 **Never share your app password** - treat it like your regular password
- 👥 **Only approve trusted contacts** - review `approved_contacts.txt` regularly
- 📝 **Review logs** - check `Logs/email_log.json` for suspicious activity
- 🔄 **Rotate passwords** - regenerate app password periodically
- 🛡️ **Use 2FA** - always keep 2-Step Verification enabled

## Gmail App Permissions

The app password grants limited access:
- ✅ Send emails from your Gmail account
- ✅ Access Gmail SMTP server
- ❌ Cannot read your emails
- ❌ Cannot access your Google Drive
- ❌ Cannot access other Google services

## Integration with AI Employee System

This server integrates with the MCP (Model Context Protocol) system:

```javascript
// In your MCP client configuration (mcp_config.json):
{
  "mcpServers": {
    "email-server": {
      "command": "node",
      "args": ["email_mcp_server.js"],
      "cwd": ".",
      "env": {
        "GMAIL_USER": "your.email@gmail.com",
        "GMAIL_APP_PASSWORD": "abcdefghijklmnop"
      }
    }
  }
}
```

## Usage Examples

### Send Quick Update

```
Tool: send_email
to: team@company.com
subject: Project Update
body: Hi Team,

The project is on track. Latest milestones:
- Phase 1: Complete ✅
- Phase 2: In Progress 🔄
- Phase 3: Starting next week

Best regards
```

### Save Draft for Review

```
Tool: draft_email
to: client@example.com
subject: Proposal Draft
body: Dear Client,

Please find attached our proposal...

[Save for review before sending]
```

### Check Pending Drafts

```
Tool: list_drafts

Response:
📋 Draft Files (2 total):
1. draft_Proposal_Draft_2026-03-04T10-30-00.md
2. draft_Client_Meeting_2026-03-03T15-00-00.md
```

## Support

For issues:
1. Check `Logs/email_log.json` for error details
2. Verify Gmail credentials in `.env`
3. Ensure recipient is in `approved_contacts.txt`
4. Test with a draft first using `draft_email` tool

## License

MIT License - Free to use and modify.
