#!/usr/bin/env python3
"""
Social Media Automation Script for Facebook and Instagram
Uses Meta Business API (Facebook Graph API)
"""

import os
import json
import time
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import requests
import schedule

# Configuration from environment
META_ACCESS_TOKEN = os.environ.get('META_ACCESS_TOKEN', '')
META_PAGE_ID = os.environ.get('META_PAGE_ID', '')
INSTAGRAM_ACCOUNT_ID = os.environ.get('INSTAGRAM_ACCOUNT_ID', '')

# Base directories
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / 'Logs'
BRIEFINGS_DIR = BASE_DIR / 'Briefings'
INBOX_DIR = BASE_DIR / 'Inbox' / 'social_posts'
PENDING_DIR = BASE_DIR / 'Pending_Approval'
APPROVED_DIR = BASE_DIR / 'Approved'

# Safety keywords that block posting
FORBIDDEN_KEYWORDS = ['lawsuit', 'complaint', 'refund', 'angry']

# Rate limiting
MAX_POSTS_PER_DAY = 5

# Ensure directories exist
for directory in [LOGS_DIR, BRIEFINGS_DIR, INBOX_DIR, PENDING_DIR, APPROVED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def log_action(action: str, details: dict, result: str = 'success') -> None:
    """Log actions to ./Logs/social_log.json"""
    log_file = LOGS_DIR / 'social_log.json'
    
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []
    
    logs.append({
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details,
        'result': result
    })
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)


def check_content_safety(content: str) -> tuple[bool, list]:
    """Check if content contains forbidden keywords"""
    content_lower = content.lower()
    found_keywords = [kw for kw in FORBIDDEN_KEYWORDS if kw in content_lower]
    return len(found_keywords) == 0, found_keywords


def get_daily_post_count() -> int:
    """Count posts made today across both platforms"""
    log_file = LOGS_DIR / 'social_log.json'
    if not log_file.exists():
        return 0
    
    today = datetime.now().date()
    count = 0
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        for entry in logs:
            if entry.get('result') == 'success':
                action = entry.get('action', '')
                if action in ['post_to_facebook', 'post_to_instagram']:
                    entry_date = datetime.fromisoformat(entry['timestamp']).date()
                    if entry_date == today:
                        count += 1
    except (json.JSONDecodeError, IOError):
        pass
    
    return count


def save_to_pending(content: str, platform: str, image_path: Optional[str] = None) -> str:
    """Save post to Pending_Approval/ folder"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{platform}_{timestamp}.md"
    filepath = PENDING_DIR / filename
    
    md_content = f"""# Pending Social Media Post

## Platform
{platform.capitalize()}

## Created
{datetime.now().isoformat()}

## Content
{content}

## Image
{image_path if image_path else 'None'}

## Status
PENDING APPROVAL

---
*Move this file to Approved/ folder to authorize posting*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    log_action('save_to_pending', {'platform': platform, 'file': str(filename)})
    return str(filename)


def check_approval(filename: str) -> bool:
    """Check if a pending file has been moved to Approved/"""
    pending_path = PENDING_DIR / filename
    approved_path = APPROVED_DIR / filename
    
    if pending_path.exists():
        return False
    if approved_path.exists():
        return True
    return False


def post_to_facebook(text: str, image_path: Optional[str] = None) -> dict:
    """
    Posts text (and optional image) to Facebook Page
    
    Args:
        text: Post text content
        image_path: Optional path to image file
    
    Returns:
        dict with post status and details
    """
    # Safety check
    is_safe, found_keywords = check_content_safety(text)
    if not is_safe:
        error_msg = f"Content blocked: contains forbidden keywords: {found_keywords}"
        log_action('post_to_facebook', {'text_preview': text[:100], 'blocked': True}, 'error')
        return {'success': False, 'error': error_msg}
    
    # Rate limit check
    daily_count = get_daily_post_count()
    if daily_count >= MAX_POSTS_PER_DAY:
        error_msg = f"Daily post limit reached ({MAX_POSTS_PER_DAY} posts)"
        log_action('post_to_facebook', {'blocked': True, 'reason': 'rate_limit'}, 'error')
        return {'success': False, 'error': error_msg}
    
    # Save to pending first
    pending_file = save_to_pending(text, 'facebook', image_path)
    
    return {
        'success': True,
        'status': 'pending',
        'pending_file': pending_file,
        'message': 'Post saved to Pending_Approval/. Move to Approved/ to publish.',
        'platform': 'facebook'
    }


def _execute_facebook_post(text: str, image_path: Optional[str] = None) -> dict:
    """
    Internal function to actually execute the Facebook post after approval.
    """
    try:
        url = f"https://graph.facebook.com/v19.0/{META_PAGE_ID}/feed"
        
        params = {
            'message': text,
            'access_token': META_ACCESS_TOKEN
        }
        
        if image_path and os.path.exists(image_path):
            # Upload photo
            url = f"https://graph.facebook.com/v19.0/{META_PAGE_ID}/photos"
            files = {'source': open(image_path, 'rb')}
            response = requests.post(url, data=params, files=files)
            files['source'].close()
        else:
            # Text-only post
            response = requests.post(url, data=params)
        
        result = response.json()
        
        if 'id' in result:
            log_action('post_to_facebook', {
                'text_preview': text[:100],
                'image': image_path,
                'post_id': result['id']
            }, 'success')
            return {
                'success': True,
                'post_id': result['id'],
                'platform': 'facebook'
            }
        else:
            error = result.get('error', {}).get('message', 'Unknown error')
            log_action('post_to_facebook', {'error': error}, 'error')
            return {'success': False, 'error': error}
            
    except Exception as e:
        log_action('post_to_facebook', {'error': str(e)}, 'error')
        return {'success': False, 'error': str(e)}


def post_to_instagram(image_path: str, caption: str) -> dict:
    """
    Posts image + caption to Instagram Business account
    
    Args:
        image_path: Path to image file (must exist locally)
        caption: Instagram caption
    
    Returns:
        dict with post status and details
    """
    # Validate image exists
    if not os.path.exists(image_path):
        error_msg = f"Image not found: {image_path}"
        log_action('post_to_instagram', {'image_path': image_path, 'blocked': True}, 'error')
        return {'success': False, 'error': error_msg}
    
    # Safety check
    is_safe, found_keywords = check_content_safety(caption)
    if not is_safe:
        error_msg = f"Content blocked: contains forbidden keywords: {found_keywords}"
        log_action('post_to_instagram', {'caption_preview': caption[:100], 'blocked': True}, 'error')
        return {'success': False, 'error': error_msg}
    
    # Rate limit check
    daily_count = get_daily_post_count()
    if daily_count >= MAX_POSTS_PER_DAY:
        error_msg = f"Daily post limit reached ({MAX_POSTS_PER_DAY} posts)"
        log_action('post_to_instagram', {'blocked': True, 'reason': 'rate_limit'}, 'error')
        return {'success': False, 'error': error_msg}
    
    # Save to pending first
    pending_file = save_to_pending(caption, 'instagram', image_path)
    
    return {
        'success': True,
        'status': 'pending',
        'pending_file': pending_file,
        'message': 'Post saved to Pending_Approval/. Move to Approved/ to publish.',
        'platform': 'instagram'
    }


def _execute_instagram_post(image_path: str, caption: str) -> dict:
    """
    Internal function to actually execute the Instagram post after approval.
    """
    try:
        # Step 1: Create media container
        container_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
        
        # Get absolute path for the image
        abs_image_path = os.path.abspath(image_path)
        
        container_params = {
            'image_url': f'file://{abs_image_path}',
            'caption': caption,
            'access_token': META_ACCESS_TOKEN
        }
        
        # For local files, we need to upload to a publicly accessible URL first
        # This is a limitation of the Instagram API - it requires a public URL
        # For now, we'll use the local path approach which works with some setups
        # In production, upload to a CDN first
        
        container_response = requests.post(container_url, data=container_params)
        container_result = container_response.json()
        
        if 'id' not in container_result:
            error = container_result.get('error', {}).get('message', 'Failed to create media container')
            log_action('post_to_instagram', {'error': error}, 'error')
            return {'success': False, 'error': error}
        
        container_id = container_result['id']
        
        # Step 2: Publish the media
        publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': META_ACCESS_TOKEN
        }
        
        publish_response = requests.post(publish_url, data=publish_params)
        publish_result = publish_response.json()
        
        if 'id' in publish_result:
            log_action('post_to_instagram', {
                'caption_preview': caption[:100],
                'image': image_path,
                'post_id': publish_result['id']
            }, 'success')
            return {
                'success': True,
                'post_id': publish_result['id'],
                'platform': 'instagram'
            }
        else:
            error = publish_result.get('error', {}).get('message', 'Failed to publish')
            log_action('post_to_instagram', {'error': error}, 'error')
            return {'success': False, 'error': error}
            
    except Exception as e:
        log_action('post_to_instagram', {'error': str(e)}, 'error')
        return {'success': False, 'error': str(e)}


def get_facebook_summary() -> dict:
    """
    Fetches last 7 days: total posts, total reach, total engagement
    Saves summary to ./Briefings/facebook_summary.md
    
    Returns:
        dict with summary data
    """
    try:
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Get posts insights
        url = f"https://graph.facebook.com/v19.0/{META_PAGE_ID}/insights"
        params = {
            'metric': 'post_impressions,post_engagements,page_posts',
            'since': seven_days_ago,
            'until': datetime.now().strftime('%Y-%m-%d'),
            'access_token': META_ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        # Parse insights
        total_reach = 0
        total_engagement = 0
        total_posts = 0
        
        if 'data' in result:
            for metric in result['data']:
                if metric['name'] == 'post_impressions' and 'values' in metric:
                    total_reach = sum(v.get('value', 0) for v in metric['values'])
                elif metric['name'] == 'post_engagements' and 'values' in metric:
                    total_engagement = sum(v.get('value', 0) for v in metric['values'])
                elif metric['name'] == 'page_posts' and 'values' in metric:
                    total_posts = sum(v.get('value', 0) for v in metric['values'])
        
        # Create summary markdown
        summary_md = f"""# Facebook Summary - Last 7 Days

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Metrics

| Metric | Value |
|--------|-------|
| Total Posts | {total_posts} |
| Total Reach | {total_reach:,} |
| Total Engagement | {total_engagement:,} |
| Avg Engagement/Post | {total_engagement / total_posts if total_posts > 0 else 0:.1f} |

## Period
From: {seven_days_ago}
To: {datetime.now().strftime('%Y-%m-%d')}

---
*Generated by Social Media Watcher*
"""
        
        # Save to Briefings
        summary_file = BRIEFINGS_DIR / 'facebook_summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_md)
        
        log_action('get_facebook_summary', {
            'total_posts': total_posts,
            'total_reach': total_reach,
            'total_engagement': total_engagement
        }, 'success')
        
        return {
            'success': True,
            'total_posts': total_posts,
            'total_reach': total_reach,
            'total_engagement': total_engagement,
            'summary_file': str(summary_file)
        }
        
    except Exception as e:
        log_action('get_facebook_summary', {'error': str(e)}, 'error')
        return {'success': False, 'error': str(e)}


def get_instagram_summary() -> dict:
    """
    Fetches last 7 days: follower count, post count, avg engagement
    Saves summary to ./Briefings/instagram_summary.md
    
    Returns:
        dict with summary data
    """
    try:
        # Get Instagram insights
        url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/insights"
        params = {
            'metric': 'follower_count,impressions,engagement',
            'access_token': META_ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        # Parse insights
        follower_count = 0
        total_impressions = 0
        total_engagement = 0
        post_count = 0
        
        if 'data' in result:
            for metric in result['data']:
                if metric['name'] == 'follower_count' and 'values' in metric:
                    follower_count = metric['values'][-1].get('value', 0) if metric['values'] else 0
                elif metric['name'] == 'impressions' and 'values' in metric:
                    total_impressions = sum(v.get('value', 0) for v in metric['values'])
                elif metric['name'] == 'engagement' and 'values' in metric:
                    total_engagement = sum(v.get('value', 0) for v in metric['values'])
        
        # Get media count from recent posts
        media_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
        media_params = {
            'fields': 'id,timestamp',
            'limit': 100,
            'access_token': META_ACCESS_TOKEN
        }
        
        media_response = requests.get(media_url, params=media_params)
        media_result = media_response.json()
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        if 'data' in media_result:
            for post in media_result['data']:
                post_date = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                if post_date >= seven_days_ago:
                    post_count += 1
        
        avg_engagement = total_engagement / post_count if post_count > 0 else 0
        
        # Create summary markdown
        summary_md = f"""# Instagram Summary - Last 7 Days

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Metrics

| Metric | Value |
|--------|-------|
| Follower Count | {follower_count:,} |
| Posts (7 days) | {post_count} |
| Total Impressions | {total_impressions:,} |
| Total Engagement | {total_engagement:,} |
| Avg Engagement/Post | {avg_engagement:.1f} |

## Period
From: {seven_days_ago.strftime('%Y-%m-%d')}
To: {datetime.now().strftime('%Y-%m-%d')}

---
*Generated by Social Media Watcher*
"""
        
        # Save to Briefings
        summary_file = BRIEFINGS_DIR / 'instagram_summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_md)
        
        log_action('get_instagram_summary', {
            'follower_count': follower_count,
            'post_count': post_count,
            'total_engagement': total_engagement
        }, 'success')
        
        return {
            'success': True,
            'follower_count': follower_count,
            'post_count': post_count,
            'avg_engagement': avg_engagement,
            'summary_file': str(summary_file)
        }
        
    except Exception as e:
        log_action('get_instagram_summary', {'error': str(e)}, 'error')
        return {'success': False, 'error': str(e)}


def process_pending_posts() -> None:
    """Check Approved/ folder and execute posts that have been approved"""
    for approved_file in APPROVED_DIR.glob('*.md'):
        # Check if already processed
        processed_marker = APPROVED_DIR / f"{approved_file.stem}.processed"
        if processed_marker.exists():
            continue
        
        # Read the approved file
        with open(approved_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse content
        platform = None
        text_content = None
        image_path = None
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().lower() == 'facebook' or line.strip().lower() == 'instagram':
                platform = line.strip().lower()
            elif line.strip().startswith('## Content'):
                # Get content from next section
                j = i + 1
                content_lines = []
                while j < len(lines) and not lines[j].startswith('##'):
                    content_lines.append(lines[j])
                    j += 1
                text_content = '\n'.join(content_lines).strip()
            elif line.strip().startswith('## Image'):
                j = i + 1
                while j < len(lines) and not lines[j].startswith('##'):
                    img_line = lines[j].strip()
                    if img_line and img_line.lower() != 'none':
                        image_path = img_line
                    j += 1
        
        if platform and text_content:
            if platform == 'facebook':
                result = _execute_facebook_post(text_content, image_path)
            elif platform == 'instagram':
                if image_path:
                    result = _execute_instagram_post(image_path, text_content)
                else:
                    result = {'success': False, 'error': 'Instagram requires an image'}
            
            # Mark as processed
            if result.get('success'):
                with open(processed_marker, 'w') as f:
                    f.write(f"Processed at {datetime.now().isoformat()}\n")
                    f.write(f"Result: {json.dumps(result)}\n")


def check_inbox_for_posts() -> None:
    """Check Inbox/social_posts/ for new post files every 30 minutes"""
    for post_file in INBOX_DIR.glob('*.txt'):
        filename = post_file.name.lower()
        
        # Determine platform from filename
        if filename.startswith('facebook_'):
            platform = 'facebook'
        elif filename.startswith('instagram_'):
            platform = 'instagram'
        else:
            continue
        
        # Read content
        with open(post_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Parse content - first line is text, second line (if exists) is image path
        lines = content.split('\n', 1)
        text = lines[0]
        image = lines[1] if len(lines) > 1 else None
        
        # Submit to appropriate function
        if platform == 'facebook':
            result = post_to_facebook(text, image)
        else:
            if image:
                result = post_to_instagram(image, text)
            else:
                result = {'success': False, 'error': 'Instagram requires an image path'}
        
        # Move processed file
        if result.get('success'):
            # Move to pending (already done by post functions)
            post_file.unlink()
            log_action('inbox_processed', {'file': filename, 'platform': platform})


def run_scheduler() -> None:
    """Run the scheduler to check inbox every 30 minutes"""
    schedule.every(30).minutes.do(check_inbox_for_posts)
    schedule.every(30).minutes.do(process_pending_posts)
    
    print("Social Media Watcher started. Checking inbox every 30 minutes...")
    print("Press Ctrl+C to stop.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'post-facebook':
            text = sys.argv[2] if len(sys.argv) > 2 else ''
            image = sys.argv[3] if len(sys.argv) > 3 else None
            result = post_to_facebook(text, image)
            print(json.dumps(result, indent=2))
        
        elif command == 'post-instagram':
            image = sys.argv[2] if len(sys.argv) > 2 else ''
            caption = sys.argv[3] if len(sys.argv) > 3 else ''
            result = post_to_instagram(image, caption)
            print(json.dumps(result, indent=2))
        
        elif command == 'facebook-summary':
            result = get_facebook_summary()
            print(json.dumps(result, indent=2))
        
        elif command == 'instagram-summary':
            result = get_instagram_summary()
            print(json.dumps(result, indent=2))
        
        elif command == 'process':
            process_pending_posts()
            print("Processed pending posts.")
        
        elif command == 'watch':
            run_scheduler()
        
        else:
            print(f"Unknown command: {command}")
            print("Usage:")
            print("  python social_media_watcher.py post-facebook <text> [image_path]")
            print("  python social_media_watcher.py post-instagram <image_path> <caption>")
            print("  python social_media_watcher.py facebook-summary")
            print("  python social_media_watcher.py instagram-summary")
            print("  python social_media_watcher.py process")
            print("  python social_media_watcher.py watch")
    else:
        print("Social Media Watcher - Meta Business API Integration")
        print("Run with 'watch' to start scheduler, or use specific commands.")
        print("Example: python social_media_watcher.py watch")
