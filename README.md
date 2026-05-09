# BossFinder

Multi-agent CrewAI system that finds key people and all their contact channels at any company.

## Architecture

```
POST /search { "company": "Stripe" }
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  CrewAI Crew (sequential process)                   │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  LinkedIn    │  │  Twitter/X   │  │  Email   │  │
│  │  Agent       │  │  Agent       │  │  Agent   │  │
│  │  Proxycurl   │  │  Twitter API │  │  Hunter  │  │
│  │  + Serper    │  │  + Serper    │  │  Apollo  │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  GitHub      │  │  News        │  │  Web     │  │
│  │  Agent       │  │  Agent       │  │  Search  │  │
│  │  GitHub API  │  │  NewsAPI     │  │  Serper  │  │
│  │              │  │  + Serper    │  │  Tavily  │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
│                                                     │
│  ┌──────────────┐                                   │
│  │  Enrichment  │  ← Clearbit company + prospector  │
│  │  Agent       │                                   │
│  └──────────────┘                                   │
│                  ↓ all outputs as context           │
│  ┌──────────────────────────────────────────────┐   │
│  │  Merger Agent  (LLM dedup + JSON synthesis)  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
        │
        ▼
  Deterministic post-processor (rapidfuzz dedup)
        │
        ▼
  CompanySearchResult { people: [...] }
```

Each person record collects:
- Full name + title
- Email addresses (multiple, with confidence scores)
- Phone numbers
- LinkedIn URL
- Twitter / X handle
- GitHub username
- Personal website
- Location + bio
- Source list (which agents found this person)

## Setup

```bash
# 1. Clone and enter directory
cd bossfinder

# 2. Create and activate a virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and fill in the keys you have
```

## Required API keys

At minimum you need **one LLM key** and **one search key**. More keys = richer results.

| Key | Service | Where to get |
|-----|---------|--------------|
| `OPENAI_API_KEY` | GPT-4o (LLM) | platform.openai.com |
| `ANTHROPIC_API_KEY` | Claude (LLM) | console.anthropic.com |
| `SERPAPI_API_KEY` | Google/Bing search | serpapi.com |
| `TAVILY_API_KEY` | AI search | tavily.com |
| `PROXYCURL_API_KEY` | LinkedIn data | nubela.co/proxycurl |
| `TWITTER_BEARER_TOKEN` | Twitter/X API | developer.twitter.com |
| `HUNTER_API_KEY` | Email finder | hunter.io |
| `APOLLO_API_KEY` | People + email + phone | apollo.io |
| `CLEARBIT_API_KEY` | Company enrichment | clearbit.com |
| `GITHUB_TOKEN` | GitHub org members | github.com/settings/tokens |
| `NEWS_API_KEY` | News articles | newsapi.org |

Set `CREW_LLM_MODEL` to `claude-sonnet-4-6` to use Claude instead of GPT-4o.

## Run the API server

```bash
python main.py
# Server starts on http://0.0.0.0:8000
```

## API Usage

### Search for company key people

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"company": "Stripe"}'
```

```bash
# GET convenience endpoint
curl http://localhost:8000/search/Stripe
```

### Response

```json
{
  "company": "Stripe",
  "total_found": 24,
  "people": [
    {
      "name": "Patrick Collison",
      "title": "CEO & Co-founder",
      "company": "Stripe",
      "email": ["patrick@stripe.com"],
      "phone": [],
      "linkedin_url": "https://www.linkedin.com/in/patrickcollison",
      "twitter_handle": "patrickc",
      "github_username": "patrickcollison",
      "website": "https://patrickcollison.com",
      "sources": ["linkedin", "twitter", "web", "github"],
      "confidence": 0.95
    }
  ]
}
```

### Health check

```bash
curl http://localhost:8000/health
```

## CLI usage (no server)

```bash
python run_cli.py "Stripe"
```

## Interactive docs

```
http://localhost:8000/docs
```
