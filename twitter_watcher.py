#!/usr/bin/env python3
"""
Twitter/X Automation Script
Uses Tweepy with Twitter API v1.1 (Free Tier)
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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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


def get_twitter_client() -> tweepy.API:
    """Create and return authenticated Twitter API v1.1 client"""
    auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    return tweepy.API(auth, wait_on_rate_limit=True)


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
    Uses Twitter API v1.1
    """
    try:
        client = get_twitter_client()

        # Post the tweet using v1.1 API
        tweet = client.update_status(status=text)

        if tweet and tweet.id:
            tweet_id = str(tweet.id)
            tweet_url = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet_id}"

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
    Fetches last 7 days: tweet count, total likes, followers count
    Saves to ./Briefings/twitter_summary.md
    Note: Twitter API v1.1 doesn't provide impression metrics

    Returns:
        dict with summary data
    """
    try:
        client = get_twitter_client()

        # Get authenticated user's info
        me = client.verify_credentials()
        username = me.screen_name
        current_followers = me.followers_count

        # Get tweets from timeline (last 200 tweets)
        tweets = client.home_timeline(count=200)

        total_tweets = 0
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        seven_days_ago = datetime.now() - timedelta(days=7)

        # Filter tweets from last 7 days
        for tweet in tweets:
            # Check if tweet is from this user and within 7 days
            if tweet.created_at.replace(tzinfo=None) >= seven_days_ago:
                if tweet.user.id == me.id:
                    total_tweets += 1
                    total_likes += tweet.favorite_count
                    total_retweets += tweet.retweet_count
                    total_replies += 0  # Reply count not available in v1.1

        # Create summary markdown
        summary_md = f"""# Twitter Summary - Last 7 Days

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Account:** @{username}

## Metrics

| Metric | Value |
|--------|-------|
| Tweets Posted | {total_tweets} |
| Total Likes | {total_likes:,} |
| Total Retweets | {total_retweets:,} |
| Current Followers | {current_followers:,} |
| Avg Likes/Tweet | {total_likes / total_tweets if total_tweets > 0 else 0:,.1f} |

## Period
From: {seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}
To: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*Generated by Twitter Watcher*
*Note: Impressions not available in free API tier*
"""

        # Save to Briefings
        summary_file = BRIEFINGS_DIR / 'twitter_summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_md)

        log_action('get_twitter_summary', {
            'total_tweets': total_tweets,
            'total_likes': total_likes,
            'current_followers': current_followers
        }, 'success')

        return {
            'success': True,
            'total_tweets': total_tweets,
            'total_likes': total_likes,
            'total_retweets': total_retweets,
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
    Uses Twitter API v1.1

    Returns:
        dict with results
    """
    try:
        client = get_twitter_client()

        # Get authenticated user's info
        me = client.verify_credentials()
        username = me.screen_name
        user_id = me.id

        # Get mentions from last 24 hours (v1.1 API)
        mentions = client.mentions_timeline(count=100)

        matched_mentions = []
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

        for mention in mentions:
            # Filter by time (last 24 hours)
            if mention.created_at.replace(tzinfo=None) < twenty_four_hours_ago:
                continue

            text = mention.text.lower()

            # Check if contains monitored keywords
            matched_keywords = [kw for kw in MONITOR_KEYWORDS if kw in text]

            if matched_keywords:
                # Check if negative/angry - don't auto-reply to these
                is_safe, negative_keywords = check_content_safety(text)

                mention_data = {
                    'tweet_id': str(mention.id),
                    'author_username': mention.user.screen_name,
                    'author_name': mention.user.name,
                    'text': mention.text,
                    'matched_keywords': matched_keywords,
                    'created_at': mention.created_at.isoformat(),
                    'is_negative': not is_safe,
                    'negative_keywords': negative_keywords,
                    'metrics': {
                        'like_count': mention.favorite_count,
                        'retweet_count': mention.retweet_count,
                        'reply_count': 0  # Not available in v1.1
                    }
                }
                matched_mentions.append(mention_data)

                # Create action file
                create_action_file(mention_data, username)

        log_action('check_mentions', {
            'total_mentions': len(matched_mentions),
            'matched_keywords': len(matched_mentions)
        }, 'success')

        return {
            'success': True,
            'mentions_checked': len(mentions),
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
