# Skill: Process Inbox

## Purpose
Scan Needs_Action folder, analyze each item using Company_Handbook rules, create a Plan, and update Dashboard.

## Trigger
Run this skill whenever new files appear in Needs_Action/

## Steps
1. Read all .md files in Needs_Action/
2. Read Company_Handbook.md for rules
3. For each item, decide required action
4. Write Plan file in Plans/ with checkboxes
5. Update Dashboard.md with findings
6. If action requires approval, create file in Pending_Approval/ instead of acting

## Rules
- Never delete files
- Never take external action directly
- Always update Dashboard after running
- Move processed items to Done/ only after plan is written

## Output Format
Always end by printing: SKILL_COMPLETE
