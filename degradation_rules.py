#!/usr/bin/env python3
"""
Degradation Rules - Graceful Failure Handling

Defines what happens when each component fails, ensuring the system
continues operating in a degraded but safe mode.

Rules:
1. Gmail API down → Queue emails to ./Drafts/queued/
2. Odoo unreachable → Cache last known data, use cache with warning
3. Claude Code unavailable → Watchers collect to Needs_Action/, log backlog
4. Social API rate limited → Move to retry folder, max 3 retries
"""

import os
import sys
import json
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from functools import wraps

# Base directories
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / 'Logs'
DRAFTS_DIR = BASE_DIR / 'Drafts'
ACCOUNTING_DIR = BASE_DIR / 'Accounting'
INBOX_DIR = BASE_DIR / 'Inbox'
NEEDS_ACTION_DIR = BASE_DIR / 'Needs_Action'
PENDING_DIR = BASE_DIR / 'Pending_Approval'
DASHBOARD_FILE = BASE_DIR / 'Dashboard.md'

# Ensure directories exist
for directory in [LOGS_DIR, DRAFTS_DIR / 'queued', ACCOUNTING_DIR, 
                  INBOX_DIR / 'social_posts' / 'retry', NEEDS_ACTION_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# State files
DEGRADATION_STATE_FILE = LOGS_DIR / 'degradation_state.json'
ODEO_CACHE_FILE = ACCOUNTING_DIR / 'odoo_cache.json'
EMAIL_QUEUE_FILE = DRAFTS_DIR / 'queued' / 'email_queue.json'
SOCIAL_RETRY_FILE = INBOX_DIR / 'social_posts' / 'retry' / 'retry_queue.json'

# Maximum retries for social posts
MAX_SOCIAL_RETRIES = 3
SOCIAL_RETRY_DELAY_HOURS = 1


def load_degradation_state() -> Dict[str, Any]:
    """Load current degradation state"""
    if not DEGRADATION_STATE_FILE.exists():
        return {'components': {}, 'last_updated': None}
    
    try:
        with open(DEGRADATION_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'components': {}, 'last_updated': None}


def save_degradation_state(state: Dict[str, Any]) -> None:
    """Save degradation state"""
    state['last_updated'] = datetime.now().isoformat()
    with open(DEGRADATION_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def set_component_degraded(component: str, reason: str, details: Dict = None) -> None:
    """Mark a component as degraded"""
    state = load_degradation_state()
    state['components'][component] = {
        'status': 'degraded',
        'reason': reason,
        'details': details or {},
        'since': datetime.now().isoformat()
    }
    save_degradation_state(state)
    print(f"⚠️  [{component}] Marked as DEGRADED: {reason}")


def set_component_healthy(component: str) -> None:
    """Mark a component as healthy"""
    state = load_degradation_state()
    if component in state['components']:
        del state['components'][component]
        save_degradation_state(state)
        print(f"✅ [{component}] Marked as HEALTHY")


def is_component_degraded(component: str) -> bool:
    """Check if a component is currently degraded"""
    state = load_degradation_state()
    return component in state['components']


def get_degradation_info(component: str) -> Optional[Dict]:
    """Get degradation info for a component"""
    state = load_degradation_state()
    return state['components'].get(component)


# ============================================================================
# RULE 1: Gmail API Down - Queue Emails
# ============================================================================

class EmailQueueManager:
    """Manages email queue when Gmail API is unavailable"""
    
    def __init__(self):
        self.queue_file = EMAIL_QUEUE_FILE
        self.queue = self._load_queue()
    
    def _load_queue(self) -> List[Dict]:
        if not self.queue_file.exists():
            return []
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_queue(self) -> None:
        with open(self.queue_file, 'w', encoding='utf-8') as f:
            json.dump(self.queue, f, indent=2)
    
    def queue_email(self, to: str, subject: str, body: str, 
                    attachments: List[str] = None, priority: str = 'normal') -> str:
        """
        Queue an email when Gmail API is down.
        Never lose an email - always queue successfully.
        """
        email_id = f"email_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        queued_email = {
            'id': email_id,
            'to': to,
            'subject': subject,
            'body': body,
            'attachments': attachments or [],
            'priority': priority,
            'queued_at': datetime.now().isoformat(),
            'status': 'queued',
            'retry_count': 0
        }
        
        self.queue.append(queued_email)
        self._save_queue()
        
        # Also save as individual draft file
        draft_file = DRAFTS_DIR / 'queued' / f"{email_id}.md"
        draft_content = f"""# Queued Email

**ID:** {email_id}
**To:** {to}
**Subject:** {subject}
**Priority:** {priority}
**Queued At:** {queued_email['queued_at']}

---

## Body

{body}

---

## Attachments
{chr(10).join(f'- {att}' for att in attachments) if attachments else 'None'}

---
*This email was queued due to Gmail API unavailability*
*Will be sent when API is restored*
"""
        with open(draft_file, 'w', encoding='utf-8') as f:
            f.write(draft_content)
        
        print(f"📧 Email queued: {email_id} (to: {to})")
        return email_id
    
    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        return {
            'total_queued': len(self.queue),
            'oldest': self.queue[0]['queued_at'] if self.queue else None,
            'newest': self.queue[-1]['queued_at'] if self.queue else None,
            'by_priority': {
                'high': len([e for e in self.queue if e['priority'] == 'high']),
                'normal': len([e for e in self.queue if e['priority'] == 'normal']),
                'low': len([e for e in self.queue if e['priority'] == 'low'])
            }
        }
    
    def process_queue(self, send_func: Callable) -> Dict:
        """
        Process queued emails when Gmail API is restored.
        
        Args:
            send_func: Function to send email (to, subject, body, attachments)
        
        Returns:
            dict with processing results
        """
        results = {
            'sent': [],
            'failed': [],
            'remaining': []
        }
        
        for email in self.queue[:]:  # Copy list for safe iteration
            try:
                send_func(
                    to=email['to'],
                    subject=email['subject'],
                    body=email['body'],
                    attachments=email['attachments']
                )
                results['sent'].append(email['id'])
                self.queue.remove(email)
                
                # Mark draft as sent
                draft_file = DRAFTS_DIR / 'queued' / f"{email['id']}.md"
                if draft_file.exists():
                    draft_file.unlink()
                    
            except Exception as e:
                email['retry_count'] += 1
                if email['retry_count'] >= 5:
                    results['failed'].append({
                        'id': email['id'],
                        'error': str(e),
                        'retry_count': email['retry_count']
                    })
                    self.queue.remove(email)
                else:
                    results['remaining'].append(email['id'])
        
        self._save_queue()
        return results


# ============================================================================
# RULE 2: Odoo Unreachable - Use Cached Data
# ============================================================================

class OdooCacheManager:
    """Manages Odoo data cache when Odoo is unreachable"""
    
    def __init__(self):
        self.cache_file = ODEO_CACHE_FILE
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        if not self.cache_file.exists():
            return {'data': {}, 'last_updated': None, 'valid': False}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {'data': {}, 'last_updated': None, 'valid': False}
    
    def _save_cache(self) -> None:
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2)
    
    def update_cache(self, data_type: str, data: Any) -> None:
        """Update cached data (call this when Odoo is reachable)"""
        self.cache['data'][data_type] = {
            'content': data,
            'cached_at': datetime.now().isoformat()
        }
        self.cache['last_updated'] = datetime.now().isoformat()
        self.cache['valid'] = True
        self._save_cache()
    
    def get_cached_data(self, data_type: str) -> tuple[Any, bool]:
        """
        Get cached data. Returns (data, is_cached_flag).
        
        The is_cached_flag indicates whether data is from cache (True) 
        or fresh (False), so callers can add appropriate warnings.
        """
        if data_type not in self.cache['data']:
            return None, False
        
        cached = self.cache['data'][data_type]
        return cached['content'], True
    
    def get_cache_status(self) -> Dict:
        """Get cache status"""
        return {
            'valid': self.cache['valid'],
            'last_updated': self.cache['last_updated'],
            'data_types': list(self.cache['data'].keys()),
            'age_hours': self._get_cache_age_hours()
        }
    
    def _get_cache_age_hours(self) -> Optional[float]:
        if not self.cache['last_updated']:
            return None
        try:
            last_update = datetime.fromisoformat(self.cache['last_updated'])
            age = datetime.now() - last_update
            return age.total_seconds() / 3600
        except (ValueError, TypeError):
            return None
    
    def is_cache_stale(self, max_age_hours: int = 24) -> bool:
        """Check if cache is stale (older than max_age_hours)"""
        age = self._get_cache_age_hours()
        if age is None:
            return True
        return age > max_age_hours


# ============================================================================
# RULE 3: Claude Code Unavailable - Log Backlog
# ============================================================================

class ClaudeBacklogManager:
    """Manages task backlog when Claude Code is unavailable"""
    
    def __init__(self):
        self.backlog_dir = NEEDS_ACTION_DIR
    
    def get_backlog_size(self) -> int:
        """Count items in backlog"""
        count = 0
        for pattern in ['*.txt', '*.md']:
            count += len(list(self.backlog_dir.glob(pattern)))
        return count
    
    def get_backlog_status(self) -> Dict:
        """Get detailed backlog status"""
        files = []
        for pattern in ['*.txt', '*.md']:
            for f in self.backlog_dir.glob(pattern):
                try:
                    stat = f.stat()
                    files.append({
                        'name': f.name,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except OSError:
                    continue
        
        # Sort by modification time
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            'total_items': len(files),
            'oldest': files[-1]['modified'] if files else None,
            'newest': files[0]['modified'] if files else None,
            'files': files[:20]  # First 20 for preview
        }
    
    def update_dashboard_backlog(self) -> None:
        """Update Dashboard.md with backlog size"""
        status = self.get_backlog_status()
        
        backlog_info = f"""
## 📋 Claude Backlog Status

**Total Items:** {status['total_items']}
**Oldest Item:** {status['oldest'] or 'N/A'}
**Newest Item:** {status['newest'] or 'N/A'}

*Watchers continue collecting. Processing will resume when Claude returns.*

---
"""
        
        if DASHBOARD_FILE.exists():
            with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update or add backlog section
            if '## 📋 Claude Backlog' in content:
                # Replace existing section
                lines = content.split('\n')
                new_lines = []
                skip = False
                for line in lines:
                    if line.startswith('## 📋 Claude Backlog'):
                        skip = True
                        new_lines.append(backlog_info.strip())
                    elif skip and line.startswith('## '):
                        skip = False
                        new_lines.append(line)
                    elif not skip:
                        new_lines.append(line)
                content = '\n'.join(new_lines)
            else:
                # Add new section
                lines = content.split('\n')
                if len(lines) > 1:
                    content = lines[0] + '\n\n' + backlog_info.strip() + '\n\n' + '\n'.join(lines[1:])
                else:
                    content = '# AI Employee Dashboard\n\n' + backlog_info.strip()
        else:
            content = f"# AI Employee Dashboard\n\n{backlog_info.strip()}"
        
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
            f.write(content)


# ============================================================================
# RULE 4: Social API Rate Limited - Retry Queue
# ============================================================================

class SocialRetryManager:
    """Manages social media post retries when rate limited"""
    
    def __init__(self):
        self.retry_dir = INBOX_DIR / 'social_posts' / 'retry'
        self.retry_file = SOCIAL_RETRY_FILE
        self.retry_queue = self._load_queue()
    
    def _load_queue(self) -> List[Dict]:
        if not self.retry_file.exists():
            return []
        try:
            with open(self.retry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_queue(self) -> None:
        with open(self.retry_file, 'w', encoding='utf-8') as f:
            json.dump(self.retry_queue, f, indent=2)
    
    def add_to_retry(self, platform: str, content: str, 
                     image_path: str = None, reason: str = 'rate_limited') -> str:
        """
        Move post to retry folder when rate limited.
        Max 3 retries, then move to Pending_Approval for human decision.
        """
        retry_id = f"retry_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        retry_entry = {
            'id': retry_id,
            'platform': platform,
            'content': content,
            'image_path': image_path,
            'reason': reason,
            'retry_count': 0,
            'max_retries': MAX_SOCIAL_RETRIES,
            'next_retry': (datetime.now() + timedelta(hours=SOCIAL_RETRY_DELAY_HOURS)).isoformat(),
            'created_at': datetime.now().isoformat(),
            'status': 'pending_retry'
        }
        
        self.retry_queue.append(retry_entry)
        self._save_queue()
        
        # Save as file in retry folder
        retry_file = self.retry_dir / f"{retry_id}.md"
        retry_content = f"""# Social Media Post - Retry Queue

**ID:** {retry_id}
**Platform:** {platform.capitalize()}
**Retry Count:** 0/{MAX_SOCIAL_RETRIES}
**Reason:** {reason}
**Created:** {retry_entry['created_at']}
**Next Retry:** {retry_entry['next_retry']}

---

## Content

{content}

---

## Image
{image_path if image_path else 'None'}

---
*This post was rate limited and queued for retry*
*Will be retried after {SOCIAL_RETRY_DELAY_HOURS} hour(s)*
*After {MAX_SOCIAL_RETRIES} failed retries, requires human approval*
"""
        with open(retry_file, 'w', encoding='utf-8') as f:
            f.write(retry_content)
        
        print(f"🔄 Social post queued for retry: {retry_id} ({platform})")
        return retry_id
    
    def process_retry_queue(self, post_func: Callable) -> Dict:
        """
        Process retry queue. Posts ready for retry are attempted.
        
        Args:
            post_func: Function to post (platform, content, image_path)
        
        Returns:
            dict with processing results
        """
        results = {
            'posted': [],
            'requeued': [],
            'needs_approval': [],
            'failed': []
        }
        
        now = datetime.now()
        
        for entry in self.retry_queue[:]:
            # Check if ready for retry
            next_retry = datetime.fromisoformat(entry['next_retry'])
            if next_retry > now:
                continue
            
            # Attempt to post
            try:
                post_func(
                    platform=entry['platform'],
                    content=entry['content'],
                    image_path=entry['image_path']
                )
                results['posted'].append(entry['id'])
                self.retry_queue.remove(entry)
                
                # Remove retry file
                retry_file = self.retry_dir / f"{entry['id']}.md"
                if retry_file.exists():
                    retry_file.unlink()
                    
            except Exception as e:
                entry['retry_count'] += 1
                
                if entry['retry_count'] >= entry['max_retries']:
                    # Move to Pending_Approval for human decision
                    results['needs_approval'].append({
                        'id': entry['id'],
                        'platform': entry['platform'],
                        'error': str(e)
                    })
                    self._move_to_pending_approval(entry)
                    self.retry_queue.remove(entry)
                else:
                    # Requeue for next retry
                    entry['next_retry'] = (now + timedelta(hours=SOCIAL_RETRY_DELAY_HOURS)).isoformat()
                    entry['status'] = 'pending_retry'
                    results['requeued'].append(entry['id'])
        
        self._save_queue()
        return results
    
    def _move_to_pending_approval(self, entry: Dict) -> None:
        """Move failed post to Pending_Approval for human decision"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pending_file = PENDING_DIR / f"social_retry_failed_{entry['platform']}_{timestamp}.md"
        
        content = f"""# Social Media Post - Human Approval Required

**Original ID:** {entry['id']}
**Platform:** {entry['platform'].capitalize()}
**Retry Attempts:** {entry['retry_count']}/{entry['max_retries']}
**Status:** FAILED AFTER MAX RETRIES

---

## Content

{entry['content']}

---

## Image
{entry['image_path'] if entry['image_path'] else 'None'}

---

## Retry History
This post was automatically retried {entry['retry_count']} times due to rate limiting.
All attempts failed. Manual review and posting required.

## Actions
- [ ] Review content
- [ ] Check API status
- [ ] Post manually or delete
- [ ] Delete this file after action

---
*Moved from retry queue by Degradation Rules*
"""
        with open(pending_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📋 Post moved to Pending_Approval: {pending_file.name}")
    
    def get_retry_status(self) -> Dict:
        """Get retry queue status"""
        return {
            'total_queued': len(self.retry_queue),
            'by_platform': {
                'facebook': len([e for e in self.retry_queue if e['platform'] == 'facebook']),
                'instagram': len([e for e in self.retry_queue if e['platform'] == 'instagram']),
                'twitter': len([e for e in self.retry_queue if e['platform'] == 'twitter'])
            },
            'ready_for_retry': len([
                e for e in self.retry_queue 
                if datetime.fromisoformat(e['next_retry']) <= datetime.now()
            ])
        }


# ============================================================================
# Decorator for Degradation-Aware Functions
# ============================================================================

def degradation_aware(component: str, fallback: Callable = None):
    """
    Decorator that applies degradation rules when component is unavailable.
    
    Args:
        component: Component name (gmail, odoo, claude, social)
        fallback: Fallback function to call when degraded
    
    Example:
        @degradation_aware('gmail', fallback=queue_email)
        def send_email(to, subject, body):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if is_component_degraded(component):
                info = get_degradation_info(component)
                print(f"⚠️  [{component}] Degraded mode active: {info.get('reason', 'Unknown')}")
                
                if fallback:
                    return fallback(*args, **kwargs)
                else:
                    raise RuntimeError(f"Component {component} is degraded and no fallback provided")
            
            try:
                result = func(*args, **kwargs)
                # Success - mark as healthy
                set_component_healthy(component)
                return result
            except Exception as e:
                # Failure - mark as degraded
                set_component_degraded(component, str(e))
                raise
        
        return wrapper
    return decorator


# ============================================================================
# Singleton Managers for Easy Import
# ============================================================================

email_queue = EmailQueueManager()
odoo_cache = OdooCacheManager()
claude_backlog = ClaudeBacklogManager()
social_retry = SocialRetryManager()


# ============================================================================
# Main - Status Check
# ============================================================================

def main():
    """Show current degradation status"""
    print("\n" + "="*60)
    print("🔧 DEGRADATION RULES STATUS")
    print("="*60)
    
    state = load_degradation_state()
    
    if not state['components']:
        print("\n✅ All components healthy")
    else:
        print("\n⚠️  Degraded Components:")
        for component, info in state['components'].items():
            print(f"\n  {component}:")
            print(f"    Reason: {info.get('reason', 'Unknown')}")
            print(f"    Since: {info.get('since', 'Unknown')}")
    
    # Email Queue Status
    email_status = email_queue.get_queue_status()
    print(f"\n📧 Email Queue: {email_status['total_queued']} queued")
    
    # Odoo Cache Status
    cache_status = odoo_cache.get_cache_status()
    print(f"💾 Odoo Cache: {'Valid' if cache_status['valid'] else 'Invalid'} "
          f"(age: {cache_status['age_hours'] or 0:.1f}h)")
    
    # Claude Backlog Status
    backlog_status = claude_backlog.get_backlog_status()
    print(f"📋 Claude Backlog: {backlog_status['total_items']} items")
    
    # Social Retry Status
    social_status = social_retry.get_retry_status()
    print(f"🔄 Social Retry Queue: {social_status['total_queued']} queued")
    
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
