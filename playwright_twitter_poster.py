"""
Twitter Poster using Playwright (No API Keys Required)
Posts tweets by automating Twitter through browser login.
Uses persistent Chrome profile for session persistence.
"""

import os
import sys
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init
from typing import List, Optional
from playwright.sync_api import sync_playwright
from time import sleep
from random import uniform

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
APPROVED_DIR = BASE_DIR / "Approved"
PENDING_DIR = BASE_DIR / "Pending_Approval"
DONE_DIR = BASE_DIR / "Done"
LOGS_DIR = BASE_DIR / "Logs"

# Ensure directories exist
for directory in [APPROVED_DIR, PENDING_DIR, DONE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuration
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME", "")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD", "")
CHROME_PATH = os.getenv("CHROME_PATH", "")
PROFILE_PATH = os.getenv("TWITTER_PROFILE_PATH", str(BASE_DIR / ".twitter_profile"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# OpenRouter AI Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")


def log(msg, level="INFO"):
    """Log message to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = LOGS_DIR / "twitter_playwright.log"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level}] {msg}\n")
    
    if level == "ERROR":
        print(f"{Fore.RED}[{level}] {msg}")
    elif level == "SUCCESS":
        print(f"{Fore.GREEN}[{level}] {msg}")
    elif level == "WARNING":
        print(f"{Fore.YELLOW}[{level}] {msg}")
    else:
        print(f"{Fore.CYAN}[{level}] {msg}")


def generate_ai_tweet(topic):
    """Generate tweet using AI"""
    import requests
    
    if not OPENROUTER_API_KEY:
        log("OPENROUTER_API_KEY not set", "ERROR")
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "Write a professional, engaging tweet. Max 280 chars. Include 2 relevant hashtags. No emojis."},
                {"role": "user", "content": f"Write a tweet about: {topic}"}
            ],
            "max_tokens": 60,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        # Clean up
        content = content.strip('"').strip("'").strip()
        
        if len(content) > 280:
            content = content[:277] + "..."
        
        return content
        
    except Exception as e:
        log(f"AI generation error: {e}", "ERROR")
        return None


def post_tweet(content):
    """Post tweet using Playwright browser automation"""
    if DRY_RUN:
        log(f"[DRY RUN] Would post: {content[:50]}...")
        return "dry_run"
    
    if not TWITTER_USERNAME:
        log("TWITTER_USERNAME not configured", "ERROR")
        return None
    
    try:
        with sync_playwright() as p:
            chrome_executable_path = CHROME_PATH if CHROME_PATH else None
            
            log(f"Launching browser with profile: {PROFILE_PATH}")
            
            context = p.chromium.launch_persistent_context(
                executable_path=chrome_executable_path,
                user_data_dir=PROFILE_PATH,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
                viewport={"width": 1280, "height": 720},
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            
            try:
                # Go to Twitter
                log("Navigating to Twitter...")
                page.goto("https://twitter.com/home", timeout=60000)
                sleep(uniform(5, 8))
                
                # Check if logged in
                if "/login" in page.url or "/i/flow/login" in page.url:
                    log("Logging in to Twitter...", "INFO")
                    
                    try:
                        # Enter username/email
                        page.fill("input[name='text']", TWITTER_USERNAME)
                        sleep(uniform(2, 3))
                        
                        # Click Next
                        page.click("button:has-text('Next')")
                        sleep(uniform(3, 5))
                        
                        # Enter password
                        page.fill("input[name='password']", TWITTER_PASSWORD)
                        sleep(uniform(2, 3))
                        
                        # Click Login
                        page.click("button:has-text('Log in')")
                        sleep(uniform(5, 10))
                        
                        log("Login successful!", "SUCCESS")
                        
                    except Exception as e:
                        log(f"Login failed: {e}", "ERROR")
                        context.close()
                        return None
                
                # Wait for home timeline
                sleep(uniform(5, 8))
                
                # Refresh to ensure fresh state
                page.reload()
                sleep(uniform(4, 6))
                
                # Find tweet composer
                log("Finding tweet composer...")
                
                tweet_box = None
                selectors = [
                    'div[contenteditable="true"]',
                    'div[role="textbox"]',
                    'textarea[data-testid="tweetTextarea_0"]',
                    '[data-testid="tweetTextarea_0"]',
                    'div[data-testid="tweetTextarea_0"]',
                ]
                
                for selector in selectors:
                    try:
                        tweet_box = page.wait_for_selector(selector, timeout=8000)
                        if tweet_box:
                            log(f"Found composer: {selector}")
                            break
                    except:
                        continue
                
                if not tweet_box:
                    # Try clicking the Tweet button first
                    log("Trying to open composer...")
                    try:
                        page.click('a[href="/compose/tweet"]')
                        sleep(3)
                        for selector in selectors:
                            try:
                                tweet_box = page.wait_for_selector(selector, timeout=5000)
                                if tweet_box:
                                    log(f"Found composer after click: {selector}")
                                    break
                            except:
                                continue
                    except Exception as e:
                        log(f"Could not open composer: {e}", "ERROR")
                
                if not tweet_box:
                    log("Could not find tweet composer - taking screenshot", "ERROR")
                    try:
                        page.screenshot(path=str(LOGS_DIR / "twitter_error.png"))
                        log(f"Screenshot saved: {LOGS_DIR / 'twitter_error.png'}", "INFO")
                    except:
                        pass
                    context.close()
                    return None
                
                # Click and clear
                tweet_box.click()
                sleep(uniform(1, 2))
                
                page.keyboard.press("Control+A")
                sleep(0.5)
                page.keyboard.press("Delete")
                sleep(0.5)
                
                # Type content
                log(f"Typing: {content[:50]}...")
                for char in content:
                    page.keyboard.type(char, delay=uniform(30, 60))
                
                sleep(uniform(3, 5))
                
                # Find and click Post button
                log("Finding Post button...")
                
                post_btn = None
                post_selectors = [
                    'button[data-testid="tweetButton"]',
                    'button[data-testid="tweetButtonInline"]',
                    'div[role="button"] span:has-text("Post")',
                ]
                
                for selector in post_selectors:
                    try:
                        post_btn = page.wait_for_selector(selector, timeout=5000)
                        if post_btn:
                            log(f"Found Post button: {selector}")
                            break
                    except:
                        continue
                
                if not post_btn:
                    log("Post button not found", "ERROR")
                    context.close()
                    return None
                
                # Wait for button to be enabled
                for i in range(10):
                    try:
                        disabled = post_btn.get_attribute('disabled')
                        if disabled is None:
                            log("Post button enabled!")
                            break
                    except:
                        pass
                    sleep(2)
                
                # Click Post
                log("Clicking Post...")
                page.evaluate("btn => btn.click()", post_btn)
                sleep(uniform(5, 8))
                
                # Check for confirmation
                try:
                    confirmation = page.wait_for_selector('text="Your post was sent"', timeout=10000)
                    if confirmation:
                        log("Tweet posted confirmation!", "SUCCESS")
                except:
                    log("No confirmation message", "WARNING")
                
                # Get URL
                sleep(3)
                current_url = page.url
                
                if "/status/" in current_url:
                    log(f"Tweet posted! URL: {current_url}", "SUCCESS")
                    context.close()
                    return current_url
                
                # Try to get from profile
                log("Checking profile for tweet...")
                page.goto(f"https://twitter.com/{TWITTER_USERNAME}", timeout=60000)
                sleep(5)
                
                first_tweet = page.query_selector('a[href*="/status/"]')
                if first_tweet:
                    href = first_tweet.get_attribute("href")
                    tweet_url = f"https://twitter.com{href}"
                    log(f"Tweet posted! URL: {tweet_url}", "SUCCESS")
                    context.close()
                    return tweet_url
                
                context.close()
                return "posted"
                
            except Exception as e:
                log(f"Error: {e}", "ERROR")
                context.close()
                return None
                
    except Exception as e:
        log(f"Browser error: {e}", "ERROR")
        return None


def post_approved():
    """Post all approved tweets"""
    posted = []
    
    files = list(APPROVED_DIR.glob("TWITTER_*.md"))
    
    if not files:
        log("No approved tweets found", "INFO")
        return posted
    
    for filepath in files:
        log(f"Processing: {filepath.name}")
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract tweet content
        lines = content.split("\n")
        in_content = False
        tweet_text = []
        
        for line in lines:
            if "## Tweet Content" in line:
                in_content = True
                continue
            elif line.startswith("## ") and in_content:
                break
            elif in_content and line.strip():
                tweet_text.append(line)
        
        tweet = "\n".join(tweet_text).strip()
        
        if not tweet:
            log(f"No content in {filepath.name}", "ERROR")
            continue
        
        # Post
        url = post_tweet(tweet)
        
        if url:
            # Move to Done
            done_path = DONE_DIR / filepath.name
            shutil.move(str(filepath), str(done_path))
            log(f"Moved to Done: {filepath.name}", "SUCCESS")
            posted.append({"file": filepath.name, "url": url})
        else:
            log(f"Failed: {filepath.name}", "ERROR")
    
    return posted


if __name__ == "__main__":
    print(f"{Fore.CYAN}=== Twitter Poster (Playwright) ==={Style.RESET_ALL}\n")
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "post" and len(sys.argv) > 2:
            text = " ".join(sys.argv[2:])
            print(f"{Fore.GREEN}Posting: {text[:50]}...{Style.RESET_ALL}")
            result = post_tweet(text)
            if result:
                print(f"{Fore.GREEN}[OK] Posted! URL: {result}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[FAIL] Could not post{Style.RESET_ALL}")
        
        elif cmd == "ai" and len(sys.argv) > 2:
            topic = " ".join(sys.argv[2:])
            print(f"{Fore.GREEN}Generating AI tweet about: {topic}{Style.RESET_ALL}")
            tweet = generate_ai_tweet(topic)
            if tweet:
                print(f"\n{Fore.CYAN}Generated:{Style.RESET_ALL}")
                print(f"  {tweet}\n")
                # Auto-post
                print(f"{Fore.GREEN}Posting tweet...{Style.RESET_ALL}")
                result = post_tweet(tweet)
                if result:
                    print(f"{Fore.GREEN}[OK] Posted! URL: {result}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}[FAIL] Could not post{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[FAIL] Could not generate{Style.RESET_ALL}")
        
        elif cmd == "check":
            print(f"{Fore.GREEN}Posting approved tweets...{Style.RESET_ALL}")
            results = post_approved()
            if results:
                print(f"{Fore.GREEN}[OK] Posted {len(results)} tweet(s){Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[INFO] No tweets posted{Style.RESET_ALL}")
        
        elif cmd == "login":
            print(f"{Fore.GREEN}Opening browser for login...{Style.RESET_ALL}")
            with sync_playwright() as p:
                chrome_executable_path = CHROME_PATH if CHROME_PATH else None
                context = p.chromium.launch_persistent_context(
                    executable_path=chrome_executable_path,
                    user_data_dir=PROFILE_PATH,
                    headless=False,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
                page = context.pages[0]
                page.goto("https://twitter.com/login")
                print("Login in browser. Close when done.")
                try:
                    while True:
                        sleep(1)
                except KeyboardInterrupt:
                    pass
                context.close()
            print(f"{Fore.GREEN}[OK] Session saved!{Style.RESET_ALL}")
        
        else:
            print(f"{Fore.YELLOW}Usage:{Style.RESET_ALL}")
            print("  python playwright_twitter_poster.py post <text>  - Post tweet")
            print("  python playwright_twitter_poster.py ai <topic>   - AI generate & post")
            print("  python playwright_twitter_poster.py check        - Post approved")
            print("  python playwright_twitter_poster.py login        - Save login")
    else:
        print(f"{Fore.YELLOW}Usage:{Style.RESET_ALL}")
        print("  python playwright_twitter_poster.py post <text>  - Post tweet")
        print("  python playwright_twitter_poster.py ai <topic>   - AI generate & post")
        print("  python playwright_twitter_poster.py check        - Post approved")
        print("  python playwright_twitter_poster.py login        - Save login")
