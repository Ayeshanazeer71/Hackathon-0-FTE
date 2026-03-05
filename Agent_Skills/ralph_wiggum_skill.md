# Ralph Wiggum Autonomous Loop Skill

## Overview

The **Ralph Wiggum Loop** is an autonomous execution pattern that keeps Claude working on a task until it is **FULLY COMPLETE**. It intercepts Claude's exit and re-injects the prompt if the task is not done yet.

Named after Ralph Wiggum's persistence, this pattern ensures tasks don't get abandoned halfway.

---

## When to Use

Use the Ralph Wiggum Loop for:

| Scenario | Example |
|----------|---------|
| **Multi-step processing** | "Process all files in Needs_Action/ and create summary reports" |
| **Complex refactoring** | "Refactor the authentication module with full test coverage" |
| **Data migration** | "Migrate all customer records from old format to new schema" |
| **Batch operations** | "Generate invoices for all pending orders" |
| **Code generation** | "Create a complete CRUD API for the User model" |
| **Documentation** | "Document all public functions in the codebase" |

### Do NOT Use For:

- Simple one-shot queries
- Tasks with unclear completion criteria
- Interactive/debugging sessions
- Tasks that require human approval at each step

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    RALPH WIGGUM LOOP                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. Run Claude CLI with task prompt                        │
│                      ↓                                      │
│   2. Check output for completion promise string             │
│                      ↓                                      │
│   3. Found? → SUCCESS → Exit loop                           │
│      Not found? → Continue                                  │
│                      ↓                                      │
│   4. Re-run Claude with original prompt + previous output   │
│                      ↓                                      │
│   5. Repeat until max iterations reached                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Command Format

```bash
python ralph_wiggum.py \
    --prompt "YOUR TASK HERE" \
    --promise "COMPLETION_MARKER" \
    --max-iter 10 \
    --task-id "optional-task-id"
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--prompt` / `-p` | ✅ Yes | The task prompt to give to Claude |
| `--promise` / `-P` | ✅ Yes | The completion string to look for |
| `--max-iter` / `-m` | ❌ No | Maximum iterations (default: 10) |
| `--task-id` / `-t` | ❌ No | Optional task ID for tracking |
| `--timeout` | ❌ No | Timeout per iteration in seconds (default: 600) |
| `--dry-run` | ❌ No | Show what would be done without running |

---

## Completion Promise Examples

Choose a promise string that Claude will naturally output when done:

| Task Type | Good Promise Strings |
|-----------|---------------------|
| General tasks | `TASK_COMPLETE`, `DONE`, `FINISHED` |
| Processing | `ALL_PROCESSED`, `PROCESSING_COMPLETE` |
| Code generation | `CODE_COMPLETE`, `GENERATION_DONE` |
| Reports | `REPORT_COMPLETE`, `SUMMARY_DONE` |
| Fixes | `ALL_FIXED`, `FIXES_COMPLETE` |

### Prompt Engineering Tip

Include the promise in your prompt:

```bash
python ralph_wiggum.py \
    --prompt "Process all invoices and create reports. When finished, write TASK_COMPLETE" \
    --promise "TASK_COMPLETE"
```

---

## State Management

### Active Task State
Location: `./ralph_state/current_task.json`

```json
{
  "id": "20260305_143022",
  "prompt": "Process all files...",
  "promise": "TASK_COMPLETE",
  "max_iterations": 10,
  "started_at": "2026-03-05T14:30:22",
  "status": "RUNNING",
  "current_iteration": 3
}
```

### Iteration History
Location: `./ralph_state/iteration_history.json`

Contains full history of each iteration including outputs, timing, and status.

---

## Failure Handling

When max iterations are reached without completion:

1. **Task marked as FAILED** in state
2. **Full history saved** to `./Logs/failed_tasks/failed_task_<id>.json`
3. **Dashboard updated** with failure alert
4. **Log entry created** in `./Logs/ralph_log.json`

### Recovering from Failure

```bash
# Review what happened
cat ./Logs/failed_tasks/failed_task_<id>.json

# Retry with more iterations
python ralph_wiggum.py \
    --prompt "Continue from previous attempt..." \
    --promise "TASK_COMPLETE" \
    --max-iter 20 \
    --task-id "retry-<original-id>"
```

---

## Examples

### Example 1: Process Pending Files

```bash
python ralph_wiggum.py \
    --prompt "Process all files in Needs_Action/ folder. For each file, create a corresponding action plan. When all files are processed, write TASK_COMPLETE" \
    --promise "TASK_COMPLETE" \
    --max-iter 5
```

### Example 2: Generate Reports

```bash
python ralph_wiggum.py \
    --prompt "Generate monthly reports for all departments. Include revenue, expenses, and projections. Write REPORT_COMPLETE when done" \
    --promise "REPORT_COMPLETE" \
    --max-iter 8 \
    --task-id "monthly-reports-march"
```

### Example 3: Code Refactoring

```bash
python ralph_wiggum.py \
    --prompt "Refactor the authentication module to use JWT tokens. Update all related tests. Write REFACTOR_DONE when complete" \
    --promise "REFACTOR_DONE" \
    --max-iter 10
```

### Example 4: Data Migration

```bash
python ralph_wiggum.py \
    --prompt "Migrate all customer data from legacy_format to new_schema. Validate each record. Write MIGRATION_COMPLETE when done" \
    --promise "MIGRATION_COMPLETE" \
    --max-iter 15
```

---

## Logs

All Ralph Wiggum activity is logged to `./Logs/ralph_log.json`:

```json
[
  {
    "timestamp": "2026-03-05T14:30:22",
    "event": "loop_started",
    "task_id": "20260305_143022",
    "prompt_preview": "Process all files...",
    "promise": "TASK_COMPLETE",
    "max_iterations": 10
  },
  {
    "timestamp": "2026-03-05T14:35:45",
    "event": "loop_completed",
    "task_id": "20260305_143022",
    "iterations": 4,
    "status": "SUCCESS"
  }
]
```

---

## Best Practices

1. **Be specific with prompts** - Clear tasks complete faster
2. **Choose unique promises** - Avoid strings that might appear mid-task
3. **Set reasonable max-iter** - Start with 5-10, adjust based on complexity
4. **Monitor first run** - Watch iteration count to calibrate future runs
5. **Review failed tasks** - Learn why tasks didn't complete

---

## Integration with Other Systems

The Ralph Wiggum Loop can be combined with:

- **Social Media Watcher**: "Post all approved content, write POSTS_COMPLETE"
- **Twitter Watcher**: "Check all mentions and create responses, write MENTIONS_DONE"
- **Odoo MCP**: "Process all draft invoices, write INVOICES_COMPLETE"
- **Logging MCP**: "Log all actions from today, write LOGGING_DONE"

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Loop never completes | Check if promise string is too specific; Claude may not output it naturally |
| Too many iterations | Task may be too complex; break into smaller subtasks |
| Claude CLI not found | Install with: `npm install -g @anthropic-ai/claude-code` |
| Timeout errors | Increase `--timeout` value or optimize prompt |
| Task fails repeatedly | Review `./Logs/failed_tasks/` for patterns |

---

*Generated for AI Employee System*
*Version: 1.0.0*
