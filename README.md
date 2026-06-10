# 🤖 AI Digest

A Python automation system that fetches AI/ML news from 20+ sources, summarises it with Gemini 2.5 Flash, and delivers two beautifully formatted HTML emails daily — 7 AM and 7 PM (UAE/UTC+4). Runs completely free on GitHub Actions.

## What It Does

- **Fetches** from 14 RSS feeds, 4 scraped pages, 5 Reddit communities, and 7 Twitter accounts
- **Deduplicates** against a local JSON file so you never see the same story twice
- **Summarises** using Gemini 2.5 Flash (free tier) with Groq Llama 3.3 70B as fallback
- **Formats** responsive HTML emails with inline CSS (Gmail-safe)
- **Delivers** via Gmail SMTP twice a day, automated through GitHub Actions cron

## Sources

| Category | Sources |
|----------|---------|
| **Research** | ArXiv cs.AI, cs.LG, cs.CL · Papers With Code · MIT News AI |
| **Industry blogs** | HuggingFace Blog · Google DeepMind · The Batch · Sebastian Raschka |
| **Developer** | Towards Data Science · Hacker News AI · dev.to AI/ML · Hashnode AI |
| **Scraped pages** | OpenAI Blog · Anthropic News · arxiv-sanity · GitHub Trending Python |
| **Reddit** | r/MachineLearning · r/LocalLLaMA · r/artificial · r/OpenAI · r/singularity |
| **Twitter** | @karpathy · @ylecun · @AnthropicAI · @OpenAI · @GoogleDeepMind · @huggingface · @sama |

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| feedparser | RSS/Atom feed parsing |
| requests + BeautifulSoup4 + lxml | Web scraping |
| PRAW | Reddit API (official, read-only) |
| google-generativeai | Gemini 2.5 Flash API |
| openai SDK | Groq fallback (OpenAI-compatible endpoint) |
| python-dotenv | Environment variable management |
| smtplib (stdlib) | Gmail SMTP delivery |
| GitHub Actions | Free cron scheduling |
| JSON file | Deduplication (no database) |

## Project Structure

```
ai-digest/
├── src/
│   ├── main.py            # Entry point — orchestrates the full pipeline
│   ├── fetcher.py         # Orchestrates all 20+ sources + deduplication
│   ├── reddit_fetcher.py  # Reddit PRAW logic (5 subreddits)
│   ├── nitter_fetcher.py  # Twitter via Nitter RSS (7 accounts, 3 instances)
│   ├── summarizer.py      # Gemini 2.5 Flash + Groq fallback
│   ├── formatter.py       # HTML email builder (morning 7 sections / evening 4)
│   └── mailer.py          # Gmail SMTP sender
├── data/
│   └── seen_urls.json     # Deduplication state (gitignored)
├── .github/workflows/
│   └── digest.yml         # Cron: 3 AM UTC + 3 PM UTC daily
├── .env.example           # Template for all 8 required env vars
├── requirements.txt
└── CLAUDE.md              # Project specification
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/yourusername/ai-digest.git
cd ai-digest
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your actual values
```

#### Get Gemini API key (free)
1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API key** → copy the key
3. Paste into `.env` as `GEMINI_API_KEY`

#### Get Groq API key (free)
1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Click **Create API key** → copy the key
3. Paste into `.env` as `GROQ_API_KEY`

#### Get Gmail App Password
1. Enable 2-Step Verification on your Google account
2. Go to [myaccount.google.com/security](https://myaccount.google.com/security) → 2-Step Verification → App passwords
3. App: **Mail**, Device: **Other** → name it "AI Digest"
4. Copy the 16-character password into `.env` as `GMAIL_APP_PASSWORD`

#### Get Reddit API credentials (optional)
Reddit is optional — the digest runs without it.

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Scroll down → **create another app...**
3. Fill in:
   - **Name:** AI Digest Bot
   - **Type:** `script`
   - **Redirect URI:** `http://localhost:8080`
4. Click **create app**
5. `REDDIT_CLIENT_ID` = the short string under "personal use script" (below the app name)
6. `REDDIT_CLIENT_SECRET` = the "secret" field
7. `REDDIT_USER_AGENT` = `python:ai-digest-bot:v1.0 (by u/YOUR_USERNAME)`

### 3. Test locally

```bash
# Dry run — generates HTML preview, no email sent
python src/main.py --time morning --dry-run

# Open the preview in your browser
# Windows:
start "" "C:\Users\YourName\AppData\Local\Temp\digest_preview_morning.html"
# macOS/Linux:
open /tmp/digest_preview_morning.html

# Live run — sends actual email
python src/main.py --time morning
python src/main.py --time evening
```

### 4. Deploy to GitHub Actions

1. Push the repository to GitHub
2. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
3. Add these 8 repository secrets (one by one, click **New repository secret**):

| Secret name | Value |
|-------------|-------|
| `GEMINI_API_KEY` | Your Gemini API key |
| `GROQ_API_KEY` | Your Groq API key |
| `GMAIL_ADDRESS` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Your 16-char Gmail App Password |
| `RECIPIENT_EMAIL` | Who receives the digest |
| `REDDIT_CLIENT_ID` | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | Reddit app secret |
| `REDDIT_USER_AGENT` | e.g. `python:ai-digest-bot:v1.0 (by u/yourname)` |

4. Go to **Actions** → **AI Digest** → **Run workflow** to test manually

The workflow runs automatically at 3 AM UTC (7 AM UAE) and 3 PM UTC (7 PM UAE) every day.

## Email Sections

**Morning (7 sections):**
🔥 Top Stories · 🧠 New Models & Embeddings · 📦 New Tools & Frameworks ·
💬 Community Pulse · 📄 Research Papers · 💡 Techniques & Approaches · 🏷️ Trending Topics

**Evening (4 sections):**
🆕 New Since Morning · 💬 Community Pulse Evening Update · 📈 Trending Today · 🔮 What to Watch Tomorrow

## Skills Demonstrated

- **Python automation** — orchestrating multiple data sources with clean error handling
- **API integration** — Gemini, Groq, Reddit PRAW, Nitter RSS, Gmail SMTP
- **Web scraping** — BeautifulSoup + lxml for blog page extraction
- **Prompt engineering** — structured JSON output from an LLM, with fallback chain
- **Email deliverability** — inline CSS HTML emails compatible with Gmail
- **DevOps** — GitHub Actions cron jobs with secrets management
- **Data persistence** — lightweight deduplication without a database

---

Built by [Sahil](https://github.com/yourusername) · UAE · Backend engineer (NestJS, Python)
