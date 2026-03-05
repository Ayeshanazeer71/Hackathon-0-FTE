#!/bin/bash
#
# Create Daily Briefing File
# Called by cron at 8:00 AM daily
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEEDS_ACTION_DIR="$SCRIPT_DIR/Needs_Action"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)

# Create daily briefing file
BRIEFING_FILE="$NEEDS_ACTION_DIR/DAILY_BRIEFING_${DATE}.md"

cat > "$BRIEFING_FILE" << EOF
---
type: daily_briefing
created: $TIMESTAMP
priority: high
status: pending
---

# Daily Briefing - $DATE

## Morning Tasks
- [ ] Review overnight emails
- [ ] Check pending approvals in Pending_Approval/
- [ ] Review any flagged messages from WhatsApp
- [ ] Check LinkedIn engagement from previous posts

## Scheduled Actions
- [ ] Review payment logs in Logs/
- [ ] Process any items in Approved/ folder
- [ ] Update team on progress

## Notes
_Add notes here throughout the day_

---
*Created automatically by AI Employee System*
EOF

echo "Daily briefing created: $BRIEFING_FILE"
