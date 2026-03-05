# CEO Briefing Generator Skill

## Overview

The **Weekly CEO Briefing Generator** automatically creates a comprehensive "Monday Morning CEO Briefing" every Sunday at 9 PM by auditing the entire week's data across all business systems.

This is your AI-powered executive assistant that synthesizes data from accounting, social media, completed tasks, and business goals into actionable insights.

---

## What It Does

```
┌─────────────────────────────────────────────────────────────────┐
│              WEEKLY CEO BRIEFING GENERATOR                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STEP A: COLLECT DATA                                           │
│  ├── Read Done/ folder (completed tasks, last 7 days)           │
│  ├── Read Accounting/Current_Month.md (revenue data)            │
│  ├── Call Odoo MCP (odoo_get_revenue_summary)                   │
│  ├── Read Briefings/facebook_summary.md                         │
│  ├── Read Briefings/instagram_summary.md                        │
│  ├── Read Briefings/twitter_summary.md                          │
│  └── Read Business_Goals.md (targets)                           │
│                                                                 │
│  STEP B: ANALYZE WITH CLAUDE                                    │
│  └── Inject all data into business analyst prompt               │
│      Generate executive-level briefing                          │
│                                                                 │
│  STEP C: SAVE OUTPUT                                            │
│  ├── Save to Briefings/[YYYY-MM-DD]_Monday_Briefing.md          │
│  ├── Update Dashboard.md with link                              │
│  └── Log to Logs/briefing_log.json                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Briefing Sections

The generated briefing includes:

| Section | Description |
|---------|-------------|
| **1. Executive Summary** | 3 sentences max - the most important takeaway |
| **2. Revenue Performance** | Actual vs target, week-over-week trend, key drivers |
| **3. Completed Tasks** | Summary of what was accomplished, major wins |
| **4. Bottlenecks & Blockers** | Tasks that took more than expected |
| **5. Social Media Performance** | Combined reach, engagement, best platform |
| **6. Cost Optimization** | Unused subscriptions, efficiency opportunities |
| **7. Upcoming Deadlines** | Critical dates in next 14 days |
| **8. Top 3 Recommended Actions** | Prioritized by impact |

---

## Scheduling

### Linux/Mac (Crontab)

Edit crontab:
```bash
crontab -e
```

Add this line (update path):
```
0 21 * * 0 cd /path/to/your/project && python3 ceo_briefing_generator.py >> Logs/crontab_ceo_briefing.log 2>&1
```

### Windows (Task Scheduler)

Run the setup script:
```batch
setup_windows_tasks.bat
```

Or manually create task:
1. Open Task Scheduler
2. Create Basic Task: "AI Employee CEO Briefing"
3. Trigger: Weekly, Sunday, 9:00 PM
4. Action: Start a program
   - Program: `python`
   - Arguments: `ceo_briefing_generator.py`
   - Start in: `C:\Users\dell\Desktop\New folder`

---

## Manual Execution

```bash
# Generate briefing now
python ceo_briefing_generator.py

# Manual mode with prompts
python ceo_briefing_generator.py --manual
```

---

## Data Sources

### Required Files/Folders

| Source | Purpose | Required |
|--------|---------|----------|
| `Done/` | Completed tasks (last 7 days) | ✅ Yes |
| `Accounting/Current_Month.md` | Revenue data | ❌ No (graceful fallback) |
| `Briefings/facebook_summary.md` | Facebook metrics | ❌ No |
| `Briefings/instagram_summary.md` | Instagram metrics | ❌ No |
| `Briefings/twitter_summary.md` | Twitter metrics | ❌ No |
| `Business_Goals.md` | Targets for comparison | ❌ No |

### Odoo Integration

The briefing generator calls Odoo directly for revenue data:
- Requires `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD` environment variables
- Fetches current month invoices
- Calculates total invoiced, paid, and outstanding

---

## Output Files

### Briefing File
Location: `./Briefings/[YYYY-MM-DD]_Monday_Briefing.md`

Example:
```markdown
# Monday Morning CEO Briefing

**Week of:** March 3-9, 2026
**Generated:** March 9, 2026 at 9:05 PM

## Executive Summary
Revenue exceeded target by 15% this week, driven by strong invoice collection. 
Social media engagement increased 23% across all platforms. Three critical 
deadlines require attention in the next 14 days.

## Revenue Performance
...
```

### Dashboard Update
The Dashboard.md is automatically updated with:
```markdown
## 📊 Latest CEO Briefing
- **Generated:** 2026-03-09 21:05
- **File:** [2026-03-09_Monday_Briefing.md](Briefings/2026-03-09_Monday_Briefing.md)
```

### Log File
Location: `./Logs/briefing_log.json`

Contains timestamped events:
- `briefing_started`
- `data_collected`
- `briefing_completed` or `briefing_failed`

---

## Best Practices

### 1. Keep Done/ Organized
Move completed tasks to `Done/` folder promptly. The briefing analyzes everything completed in the last 7 days.

### 2. Update Business_Goals.md
Keep your targets current for accurate "actual vs target" analysis.

### 3. Run Social Summaries Before Sunday
Generate social media summaries during the week:
```bash
python social_media_watcher.py facebook-summary
python social_media_watcher.py instagram-summary
python twitter_watcher.py summary
```

### 4. Review Before Distribution
The briefing is auto-generated. Review for accuracy before sending to stakeholders.

### 5. Archive Old Briefings
Move old briefings to an archive folder monthly to keep the Briefings/ directory clean.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No completed tasks found | Ensure tasks are moved to Done/ folder |
| Odoo connection failed | Check ODOO_* environment variables |
| Claude CLI not found | Install: `npm install -g @anthropic-ai/claude-code` |
| Briefing incomplete | Check Logs/briefing_log.json for errors |
| Social data missing | Run summary commands before Sunday |

---

## Customization

### Modify Briefing Sections

Edit `build_briefing_prompt()` in `ceo_briefing_generator.py` to:
- Add new sections
- Change analysis focus
- Adjust tone/style

### Change Schedule

- **Crontab:** Edit the cron expression `0 21 * * 0`
  - Format: `minute hour day month weekday`
  - `0 21 * * 0` = Sunday at 21:00 (9 PM)

- **Windows:** Modify task in Task Scheduler

### Adjust Lookback Period

Change `get_done_files_last_7_days()`:
```python
# Change from 7 days to 14 days
seven_days_ago = datetime.now() - timedelta(days=14)
```

---

## Integration with Other Systems

The CEO Briefing Generator works with:

| System | Integration |
|--------|-------------|
| **Odoo MCP** | Revenue data via JSON-RPC |
| **Social Media Watcher** | Facebook/Instagram summaries |
| **Twitter Watcher** | Twitter metrics |
| **Ralph Wiggum Loop** | Can use for complex briefing analysis |
| **Logging MCP** | Centralized audit trail |

---

## Example Output

```markdown
# Monday Morning CEO Briefing

**Week of:** March 3-9, 2026

## Executive Summary
Strong week with 23% revenue increase and successful product launch. 
Social media reach grew by 1,500 followers. Two bottlenecks identified 
in invoice processing that need immediate attention.

## Revenue Performance

| Metric | This Week | Target | Variance |
|--------|-----------|--------|----------|
| Invoiced | $45,230 | $40,000 | +13% ✅ |
| Collected | $38,100 | $35,000 | +9% ✅ |
| Outstanding | $12,450 | $10,000 | -24% ⚠️ |

**Trend:** Revenue up 23% week-over-week

## Completed Tasks This Week
- Processed 15 invoices in Odoo
- Launched new Facebook ad campaign
- Updated customer database with 50 new entries
- Resolved 12 support tickets

## Bottlenecks
- Invoice approval took 3x longer than expected
- Social media posting delayed due to API issues

## Top 3 Recommended Actions
1. **Follow up on outstanding invoices** - $12,450 overdue
2. **Review invoice approval workflow** - Reduce processing time
3. **Schedule social media content batch** - Prevent API rate limits

---
*Briefing generated automatically by AI Employee System*
```

---

*Generated for AI Employee System*
*Version: 1.0.0*
