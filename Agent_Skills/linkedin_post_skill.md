# Skill: LinkedIn Post

## Purpose
Create and schedule LinkedIn posts for the AI Employee system. Posts are saved to Inbox/linkedin_posts/ for linkedin_watcher.py to process.

## Trigger
Run this skill when human requests a LinkedIn post to be created or scheduled.

## Steps
1. Receive post content from human (or generate from template)
2. Check content against Company_Handbook.md rules:
   - No controversial topics
   - Professional tone
   - Include relevant hashtags
3. Save post as .txt file in Inbox/linkedin_posts/
4. Create approval request in Pending_Approval/ if post mentions: products, pricing, or company announcements
5. Log the post creation in Logs/

## Rules
- Maximum 3 posts per day (enforced by linkedin_watcher.py)
- All posts must be saved as .txt files
- Include hashtags: #AI #Automation #Business (or relevant alternatives)
- Never post without approval for sensitive topics

## Output Format
Post saved to: Inbox/linkedin_posts/[POST_NAME]_[timestamp].txt

Always end by printing: SKILL_COMPLETE
