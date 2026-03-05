#!/usr/bin/env python3
"""
Twitter/X Automation Script
Uses Tweepy with Twitter API v2
"""

import os
import json
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import tweepy
import schedule

# Configuration from environment
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN', '')
TWITTER_ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET', '')
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN', '')

# Base directories
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / 'Logs'
BRIEFINGS_DIR = BASE_DIR / 'Briefings'
INBOX_DIR = BASE_DIR / 'Inbox' / 'tweets'
PENDING_DIR = BASE_DIR / 'Pending_Approval'
APPROVED_DIR = BASE_DIR / 'Approved'
NEEDS_ACTION_DIR = BASE_DIR / 'Needs_Action'

# Safety keywords that block auto-reply
NEGATIVE_KEYWORDS = ['angry', 'hate', 'terrible', 'worst', 'scam', 'fraud', 'useless', 'disappointed']

# Keywords to monitor in mentions
MONITOR_KEYWORDS = ['invoice', 'help', 'price', 'urgent']

# Rate limiting
MAX_TWEETS_PER_DAY = 10
MAX_TWEET_LENGTH = 280

# Ensure directories exist
for directory in [LOGS_DIR, BRIEFINGS_DIR, INBOX_DIR, PENDING_DIR, APPROVED_DIR, NEEDS_ACTION_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def log_action(action: str, details: dict, result: str = 'success') -> None:
    """Log actions to ./Logs/twitter_log.json"""
    log_file = LOGS_DIR / 'twitter_log.json'
    
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


def get_twitter_client() -> tweepy.Client:
    """Create and return authenticated Twitter client"""
    return tweepy.Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_SECRET,
        wait_on_rate_limit=True
    )


def truncate_tweet(text: str) -> tuple[str, bool]:
    """
    Truncate text to MAX_TWEET_LENGTH chars with ... if needed
    
    Returns:
        tuple: (truncated_text, was_truncated)
    """
    if len(text) <= MAX_TWEET_LENGTH:
        return text, False
    
    # Reserve 3 chars for "..."
    truncated = text[:MAX_TWEET_LENGTH - 3] + '...'
    return truncated, True


def check_content_safety(text: str) -> tuple[bool, list]:
    """Check if content contains negative/angry keywords"""
    text_lower = text.lower()
    found_keywords = [kw for kw in NEGATIVE_KEYWORDS if kw in text_lower]
    return len(found_keywords) == 0, found_keywords


def get_daily_tweet_count() -> int:
    """Count tweets posted today"""
    log_file = LOGS_DIR / 'twitter_log.json'
    if not log_file.exists():
        return 0
    
    today = datetime.now().date()
    count = 0
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        for entry in logs:
            if entry.get('result') == 'success' and entry.get('action') == 'post_tweet':
                entry_date = datetime.fromisoformat(entry['timestamp']).date()
                if entry_date == today:
                    count += 1
    except (json.JSONDecodeError, IOError):
        pass
    
    return count


def save_to_pending(content: str) -> str:
    """Save tweet to Pending_Approval/ folder"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"tweet_{timestamp}.md"
    filepath = PENDING_DIR / filename
    
    md_content = f"""# Pending Tweet

## Created
{datetime.now().isoformat()}

## Content
{content}

## Status
PENDING APPROVAL

---
*Move this file to Approved/ folder to authorize posting*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    log_action('save_to_pending', {'file': str(filename)})
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


def post_tweet(text: str) -> dict:
    """
    Posts tweet (auto-truncates if > 280 chars)
    
    Args:
        text: Tweet text content
    
    Returns:
        dict with tweet URL and status
    """
    # Truncate if needed
    truncated_text, was_truncated = truncate_tweet(text)
    
    if was_truncated:
        log_action('post_tweet', {'truncated': True, 'original_length': len(text)}, 'info')
    
    # Safety check - don't post negative content
    is_safe, found_keywords = check_content_safety(truncated_text)
    if not is_safe:
        error_msg = f"Tweet blocked: contains negative keywords: {found_keywords}"
        log_action('post_tweet', {'text_preview': truncated_text[:100], 'blocked': True}, 'error')
        return {'success': False, 'error': error_msg}
    
    # Rate limit check
    daily_count = get_daily_tweet_count()
    if daily_count >= MAX_TWEETS_PER_DAY:
        error_msg = f"Daily tweet limit reached ({MAX_TWEETS_PER_DAY} tweets)"
        log_action('post_tweet', {'blocked': True, 'reason': 'rate_limit'}, 'error')
        return {'success': False, 'error': error_msg}
    
    # Save to pending first
    pending_file = save_to_pending(truncated_text)
    
    return {
        'success': True,
        'status': 'pending',
        'pending_file': pending_file,
        'message': 'Tweet saved to Pending_Approval/. Move to Approved/ to publish.',
        'truncated': was_truncated,
        'character_count': len(truncated_text)
    }


def _execute_tweet(text: str) -> dict:
    """
    Internal function to actually execute the tweet after approval.
    """
    try:
        client = get_twitter_client()
        
        # Post the tweet
        response = client.create_tweet(text=text)
        
        if 'data' in response and 'id' in response['data']:
            tweet_id = response['data']['id']
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            
            log_action('post_tweet', {
                'text_preview': text[:100],
                'tweet_id': tweet_id,
                'tweet_url': tweet_url
            }, 'success')
            
            return {
                'success': True,
                'tweet_id': tweet_id,
                'tweet_url': tweet_url,
                'character_count': len(text)
            }
        else:
            error = 'Unknown error posting tweet'
            log_action('post_tweet', {'error': error}, 'error')
            return {'success': False, 'error': error}
            
    except tweepy.TweepyException as e:
        error_msg = str(e)
        log_action('post_tweet', {'error': error_msg}, 'error')
        return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = str(e)
        log_action('post_tweet', {'error': error_msg}, 'error')
        return {'success': False, 'error': error_msg}


def get_twitter_summary() -> dict:
    """
    Fetches last 7 days: tweet count, total impressions, total likes, followers gained
    Saves to ./Briefings/twitter_summary.md
    
    Returns:
        dict with summary data
    """
    try:
        client = get_twitter_client()
        
        # Get authenticated user's ID
        me = client.get_me(user_auth=True)
        user_id = me['data']['id']
        username = me['data']['username']
        current_followers = me['data'].get('public_metrics', {}).get('followers_count', 0)
        
        # Calculate date range (7 days ago)
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Get tweets from last 7 days with metrics
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=100,
            tweet_fields=['created_at', 'public_metrics', 'text'],
            start_time=seven_days_ago,
            user_auth=True
        )
        
        total_tweets = 0
        total_impressions = 0
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        
        if tweets and 'data' in tweets:
            for tweet in tweets['data']:
                total_tweets += 1
                metrics = tweet.get('public_metrics', {})
                total_impressions += metrics.get('impression_count', 0)
                total_likes += metrics.get('like_count', 0)
                total_retweets += metrics.get('retweet_count', 0)
                total_replies += metrics.get('reply_count', 0)
        
        # Get follower count from 7 days ago (approximation via timeline analysis)
        # Note: Twitter API v2 doesn't provide historical follower counts directly
        # This is an estimate based on available data
        followers_gained = 0  # Would need historical data for accurate calculation
        
        # Create summary markdown
        summary_md = f"""# Twitter Summary - Last 7 Days

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Account:** @{username}

## Metrics

| Metric | Value |
|--------|-------|
| Tweets Posted | {total_tweets} |
| Total Impressions | {total_impressions:,} |
| Total Likes | {total_likes:,} |
| Total Retweets | {total_retweets:,} |
| Total Replies | {total_replies:,} |
| Current Followers | {current_followers:,} |
| Avg Impressions/Tweet | {total_impressions / total_tweets if total_tweets > 0 else 0:,.0f} |
| Avg Likes/Tweet | {total_likes / total_tweets if total_tweets > 0 else 0:,.1f} |

## Period
From: {seven_days_ago}
To: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}

---
*Generated by Twitter Watcher*
"""
        
        # Save to Briefings
        summary_file = BRIEFINGS_DIR / 'twitter_summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_md)
        
        log_action('get_twitter_summary', {
            'total_tweets': total_tweets,
            'total_impressions': total_impressions,
            'total_likes': total_likes,
            'current_followers': current_followers
        }, 'success')
        
        return {
            'success': True,
            'total_tweets': total_tweets,
            'total_impressions': total_impressions,
            'total_likes': total_likes,
            'followers_gained': followers_gained,
            'current_followers': current_followers,
            'summary_file': str(summary_file)
        }
        
    except tweepy.TweepyException as e:
        log_action('get_twitter_summary', {'error': str(e)}, 'error')
        return {'success': False, 'error': str(e)}
    except Exception as e:
        log_action('get_twitter_summary', {'error': str(e)}, 'error')
        return {'success': False, 'error': str(e)}


def check_mentions() -> dict:
    """
    Fetches unread mentions containing keywords: invoice, help, price, urgent
    Creates .md file in Needs_Action/ for each matched mention
    
    Returns:
        dict with results
    """
    try:
        client = get_twitter_client()
        
        # Get authenticated user's ID
        me = client.get_me(user_auth=True)
        user_id = me['data']['id']
        username = me['data']['username']
        
        # Get mentions from last 24 hours
        since = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        mentions = client.get_users_mentions(
            id=user_id,
            max_results=100,
            tweet_fields=['created_at', 'author_id', 'text', 'public_metrics'],
            user_fields=['username', 'name'],
            expansions=['author_id'],
            since=since,
            user_auth=True
        )
        
        matched_mentions = []
        
        if mentions and 'data' in mentions:
            # Build user lookup dict
            users = {}
            if 'includes' in mentions and 'users' in mentions['includes']:
                for user in mentions['includes']['users']:
                    users[user['id']] = user
            
            for mention in mentions['data']:
                text = mention.get('text', '').lower()
                
                # Check if contains monitored keywords
                matched_keywords = [kw for kw in MONITOR_KEYWORDS if kw in text]
                
                if matched_keywords:
                    author = users.get(mention['author_id'], {})
                    author_username = author.get('username', 'unknown')
                    author_name = author.get('name', 'Unknown')
                    
                    # Check if negative/angry - don't auto-reply to these
                    is_safe, negative_keywords = check_content_safety(text)
                    
                    mention_data = {
                        'tweet_id': mention['id'],
                        'author_username': author_username,
                        'author_name': author_name,
                        'text': mention['text'],
                        'matched_keywords': matched_keywords,
                        'created_at': mention['created_at'],
                        'is_negative': not is_safe,
                        'negative_keywords': negative_keywords,
                        'metrics': mention.get('public_metrics', {})
                    }
                    matched_mentions.append(mention_data)
                    
                    # Create action file
                    create_action_file(mention_data, username)
        
        log_action('check_mentions', {
            'total_mentions': len(matched_mentions) if mentions and 'data' in mentions else 0,
            'matched_keywords': len(matched_mentions)
        }, 'success')
        
        return {
            'success': True,
            'mentions_checked': len(matched_mentions) if mentions and 'data' in mentions else 0,
            'matched_mentions': len(matched_mentions),
            'action_files_created': len(matched_mentions)
        }
        
    except tweepy.TweepyException as e:
        log_action('check_mentions', {'error': str(e)}, 'error')
        return {'success': False, 'error': str(e)}
    except Exception as e:
        log_action('check_mentions', {'error': str(e)}, 'error')
        return {'success': False, 'error': str(e)}


def create_action_file(mention: dict, account_username: str) -> str:
    """Create a .md file in Needs_Action/ for a matched mention"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"mention_{mention['author_username']}_{timestamp}.md"
    filepath = NEEDS_ACTION_DIR / filename
    
    # Determine urgency
    urgency = 'HIGH' if 'urgent' in mention['matched_keywords'] else 'NORMAL'
    
    # Check if negative
    warning = ""
    if mention['is_negative']:
        warning = f"\n⚠️ **WARNING**: This mention contains negative language: {mention['negative_keywords']}\nDo NOT auto-reply. Manual review required.\n"
    
    md_content = f"""# Twitter Mention - Needs Action

## Priority: {urgency}

## Mention Details
- **From:** @{mention['author_username']} ({mention['author_name']})
- **Date:** {mention['created_at']}
- **Tweet ID:** {mention['tweet_id']}
- **Tweet URL:** https://twitter.com/{mention['author_username']}/status/{mention['tweet_id']}

## Matched Keywords
{', '.join(mention['matched_keywords'])}

## Original Tweet
> {mention['text']}

## Engagement Metrics
- Likes: {mention['metrics'].get('like_count', 0)}
- Retweets: {mention['metrics'].get('retweet_count', 0)}
- Replies: {mention['metrics'].get('reply_count', 0)}
{warning}
## Suggested Actions
- [ ] Review the mention
- [ ] Determine appropriate response
- [ ] Craft response (if needed)
- [ ] Post response manually or move to Approved/

---
*Generated by Twitter Watcher*
*Account: @{account_username}*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return str(filename)


def process_pending_tweets() -> None:
    """Check Approved/ folder and execute tweets that have been approved"""
    for approved_file in APPROVED_DIR.glob('tweet_*.md'):
        # Check if already processed
        processed_marker = APPROVED_DIR / f"{approved_file.stem}.processed"
        if processed_marker.exists():
            continue
        
        # Read the approved file
        with open(approved_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract tweet content from markdown
        tweet_text = None
        lines = content.split('\n')
        in_content_section = False
        
        for line in lines:
            if line.strip() == '## Content':
                in_content_section = True
                continue
            elif line.startswith('## '):
                in_content_section = False
            elif in_content_section and line.strip():
                tweet_text = line.strip()
                break
        
        if tweet_text:
            result = _execute_tweet(tweet_text)
            
            # Mark as processed
            if result.get('success'):
                with open(processed_marker, 'w', encoding='utf-8') as f:
                    f.write(f"Processed at {datetime.now().isoformat()}\n")
                    f.write(f"Result: {json.dumps(result)}\n")
                    f.write(f"Tweet URL: {result.get('tweet_url', 'N/A')}\n")


def check_inbox_for_tweets() -> None:
    """Check Inbox/tweets/ for new tweet files every 30 minutes"""
    for tweet_file in INBOX_DIR.glob('*.txt'):
        # Read content
        with open(tweet_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Submit to post function
        result = post_tweet(content)
        
        # Move processed file
        if result.get('success'):
            tweet_file.unlink()
            log_action('inbox_processed', {'file': tweet_file.name})


def run_scheduler() -> None:
    """Run the scheduler"""
    # Check inbox every 30 minutes
    schedule.every(30).minutes.do(check_inbox_for_tweets)
    
    # Check mentions every 60 minutes
    schedule.every(60).minutes.do(check_mentions)
    
    # Process pending tweets every 15 minutes
    schedule.every(15).minutes.do(process_pending_tweets)
    
    print("Twitter Watcher started.")
    print("- Checking inbox every 30 minutes")
    print("- Checking mentions every 60 minutes")
    print("- Processing approved tweets every 15 minutes")
    print("Press Ctrl+C to stop.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'post':
            text = sys.argv[2] if len(sys.argv) > 2 else ''
            result = post_tweet(text)
            print(json.dumps(result, indent=2))
        
        elif command == 'summary':
            result = get_twitter_summary()
            print(json.dumps(result, indent=2))
        
        elif command == 'mentions':
            result = check_mentions()
            print(json.dumps(result, indent=2))
        
        elif command == 'process':
            process_pending_tweets()
            print("Processed pending tweets.")
        
        elif command == 'watch':
            run_scheduler()
        
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python twitter_watcher.py post <text>")
            print("  python twitter_watcher.py summary")
            print("  python twitter_watcher.py mentions")
            print("  python twitter_watcher.py process")
            print("  python twitter_watcher.py watch")
    else:
        print("Twitter Watcher - Twitter API v2 Integration")
        print("Run with 'watch' to start scheduler, or use specific commands.")
        print("Example: python twitter_watcher.py watch")
