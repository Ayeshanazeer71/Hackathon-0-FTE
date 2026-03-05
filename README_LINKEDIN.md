# LinkedIn Poster Service

An automated LinkedIn posting service that generates professional content using AI and publishes approved posts to LinkedIn.

## Features

- 🤖 **AI-Powered Content Generation** - Creates engaging LinkedIn posts using GPT-4, Claude, or Qwen
- ✅ **Approval Workflow** - Review content before publishing (Pending → Approved → Done)
- ⏰ **Auto-Scheduler** - Automatically posts approved content at configurable intervals
- 📝 **Dry Run Mode** - Test without actually posting
- 📊 **Activity Logging** - All actions logged to JSON files
- 🔒 **Safe by Default** - Requires manual approval before posting

## Directory Structure

```
AI_Employee_Vault/
├── Pending_Approval/   ← AI-generated posts wait here for review
├── Approved/           ← Move files here to schedule for posting
├── Done/               ← Successfully posted content archived here
└── Logs/               ← Daily JSON activity logs
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit the `.env` file with your credentials:

```bash
# LinkedIn API (Required for posting)
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_AUTHOR_URN=urn:li:person:your_id_here

# AI Provider (Choose one)
OPENROUTER_API_KEY=sk-or-v1-xxxxx        # For GPT-4, Claude, etc.
# OR
QWEN_API_KEY=your_qwen_key               # For Qwen models

# Application Settings
DRY_RUN=false           # Set to true for testing
POST_INTERVAL=600       # Check every 10 minutes
```

### 3. Get LinkedIn API Credentials

#### Step 1: Create LinkedIn Developer Account

1. Go to https://www.linkedin.com/developers/
2. Sign in and create a developer account

#### Step 2: Create an App

1. Visit https://www.linkedin.com/developers/apps
2. Click **"Create app"**
3. Fill in:
   - App name (e.g., "AI Employee LinkedIn Poster")
   - Upload a logo (required)
   - Link to a LinkedIn Company Page (required)

#### Step 3: Request Permissions

Go to your app's **Auth** tab and request these scopes:

| Permission | Purpose | Required |
|------------|---------|----------|
| `r_liteprofile` | Read basic profile | ✅ Yes |
| `w_member_social` | Post on behalf of user | ✅ Yes |
| `openid` | Get user ID | ✅ Yes |
| `profile` | Access profile info | ✅ Yes |
| `r_member_social` | Read posts (optional) | ⚠️ Optional |

**Note:** Permission approval may take 1-2 business days.

#### Step 4: Generate Access Token

**Option A: Using OAuth 2.0 (Recommended for Production)**

1. Construct authorization URL:
   ```
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=r_liteprofile%20w_member_social%20openid%20profile
   ```

2. Authorize the app and get the authorization code

3. Exchange code for token:
   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -d "grant_type=authorization_code" \
     -d "code=YOUR_AUTH_CODE" \
     -d "redirect_uri=YOUR_REDIRECT_URI" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET"
   ```

**Option B: Generate Test Token (Quick Setup)**

1. Go to your app dashboard
2. Navigate to **Auth** → **Generate Token**
3. Select scopes and generate
4. Copy the token (starts with `AQ...`)

#### Step 5: Get Your Author URN

Run the built-in command:

```bash
python linkedin_poster.py --whoami
```

Output will show:
```
Your user ID (sub): 8heXqukEv1
Add to .env:
LINKEDIN_AUTHOR_URN=urn:li:person:8heXqukEv1
```

Copy the URN to your `.env` file.

### 4. Test Your Setup

```bash
# Test connection (shows your URN)
python linkedin_poster.py --whoami

# Generate a test post
python linkedin_poster.py -g "AI in healthcare"

# List pending posts
python linkedin_poster.py --list

# Test post (with DRY_RUN=true)
python linkedin_poster.py --post --dry-run
```

## Usage

### Generate a LinkedIn Post

Creates AI-generated content and saves to `Pending_Approval/`:

```bash
python linkedin_poster.py -g "Your topic here"
# Example:
python linkedin_poster.py -g "The future of remote work"
```

### Review and Approve Content

1. Check generated posts:
   ```bash
   python linkedin_poster.py --list
   ```

2. Review the file in `AI_Employee_Vault/Pending_Approval/`

3. Move to `Approved/` when ready:
   ```bash
   # Windows PowerShell
   Move-Item AI_Employee_Vault/Pending_Approval/LINKEDIN_*.md AI_Employee_Vault/Approved/
   
   # Linux/Mac
   mv AI_Employee_Vault/Pending_Approval/LINKEDIN_*.md AI_Employee_Vault/Approved/
   ```

### Post to LinkedIn

**Manual posting:**
```bash
python linkedin_poster.py --post
```

**Auto-scheduler (runs continuously):**
```bash
python linkedin_poster.py --schedule
```

The scheduler checks every 10 minutes (configurable via `POST_INTERVAL`) for approved posts and publishes them automatically.

### Command Reference

| Command | Description |
|---------|-------------|
| `python linkedin_poster.py -g "topic"` | Generate a new post about a topic |
| `python linkedin_poster.py --post` | Post all approved content now |
| `python linkedin_poster.py --list` | List pending and approved posts |
| `python linkedin_poster.py --schedule` | Run auto-scheduler (default) |
| `python linkedin_poster.py --whoami` | Get your LinkedIn person URN |
| `python linkedin_poster.py --test-linkedin` | Verify API connection |
| `python linkedin_poster.py --dry-run` | Simulate without posting |

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LINKEDIN_ACCESS_TOKEN` | - | LinkedIn API access token |
| `LINKEDIN_AUTHOR_URN` | - | Your LinkedIn URN (e.g., `urn:li:person:XXXXX`) |
| `OPENROUTER_API_KEY` | - | OpenRouter API key (for GPT-4, Claude) |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model to use via OpenRouter |
| `QWEN_API_KEY` | - | Qwen/Dashscope API key |
| `QWEN_MODEL` | `qwen-plus` | Qwen model to use |
| `DRY_RUN` | `false` | If `true`, simulate without posting |
| `POST_INTERVAL` | `600` | Seconds between scheduler checks |

### AI Model Options

**OpenRouter** (supports multiple providers):
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=anthropic/claude-3-sonnet
# Other options: openai/gpt-4-turbo, meta-llama/llama-3-70b-instruct, etc.
```

**Qwen** (Alibaba Cloud):
```env
QWEN_API_KEY=your_key
QWEN_MODEL=qwen-max
# Other options: qwen-plus, qwen-turbo
```

## Approval Workflow

```
┌─────────────────┐     Review     ┌─────────────────┐     Auto-post    ┌─────────────────┐
│   Pending_      │ ──────────────> │    Approved/    │ ───────────────> │      Done/      │
│   Approval/     │   (manual)      │                 │   (scheduler)    │                 │
└─────────────────┘                 └─────────────────┘                  └─────────────────┘
       ↑                                    │                                    │
       │                                    │                                    │
  AI generates                         Move file here                        Posted successfully
  content here                         to schedule                           and archived
```

## Example Post Format

Generated files include frontmatter metadata:

```markdown
---
type: linkedin_post
topic: AI in healthcare
generated: 2026-03-04T00:13:58
status: pending_approval
---
## Post Content

🚀 AI is revolutionizing healthcare faster than ever before!

[Main content with insights and advice...]

What's your take on AI in healthcare? Share your thoughts below! 👇

#AI #Healthcare #DigitalHealth #Innovation #MedTech

## To Approve
Move this file to /Approved/ folder to schedule for posting.
```

## Troubleshooting

### "LINKEDIN_ACCESS_TOKEN not set"
- Check `.env` file exists in project root
- Ensure token is copied correctly (no extra spaces)
- Restart the script after editing `.env`

### "Author URN must match the account"
- Run `python linkedin_poster.py --whoami` to get correct URN
- Update `LINKEDIN_AUTHOR_URN` in `.env`
- URN format: `urn:li:person:XXXXX` or `urn:li:member:XXXXX`

### "Not enough permissions" (403 error)
- Verify app has `w_member_social` permission
- Regenerate token with correct scopes
- Wait for permission approval (1-2 business days)

### "AI client not initialized"
- Set either `OPENROUTER_API_KEY` or `QWEN_API_KEY` in `.env`
- Check API key is valid and has credits

### Post generated but not posting
- Check `DRY_RUN=false` in `.env`
- Move file from `Pending_Approval/` to `Approved/`
- Run `python linkedin_poster.py --post`

## Logs

Activity logs are saved to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
[
  {
    "type": "linkedin_post_generated",
    "timestamp": "2026-03-04T00:13:58",
    "data": {
      "topic": "AI in healthcare",
      "file": "LINKEDIN_ai_in_healthcare_20260304_001358.md",
      "content_length": 1364
    }
  },
  {
    "type": "linkedin_post_success",
    "timestamp": "2026-03-04T01:08:28",
    "data": {
      "topic": "AI in healthcare",
      "post_id": "urn:li:share:7434691182045323264",
      "length": 1364
    }
  }
]
```

## Security Best Practices

- 🔐 Never commit `.env` to version control
- 🔑 Rotate API tokens regularly
- 🛡️ Use minimum required permissions
- 📝 Review all AI-generated content before approving
- 🧪 Test with `DRY_RUN=true` first

## License

MIT License - Feel free to use and modify for your projects.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `AI_Employee_Vault/Logs/`
3. Run with `--dry-run` to debug without posting
