# BossFinder

> **Multi-agent company intelligence — find the key people and every contact channel at any company.**

BossFinder is an open-source CrewAI system that accepts a company name and fans out to 8 specialized agents, each mining a different data source (LinkedIn, Twitter/X, GitHub, Hunter.io, Apollo.io, Clearbit, NewsAPI, and the open web). Results are deduplicated and merged into a single clean JSON contact list, then served through a FastAPI endpoint.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![CrewAI](https://img.shields.io/badge/built%20with-CrewAI-blueviolet)](https://crewai.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com)

---

## Table of Contents

- [Architecture](#architecture)
- [What it collects](#what-it-collects)
- [API keys reference](#api-keys-reference)
- [Setup](#setup)
  - [Option A — Python virtualenv](#option-a--python-virtualenv)
  - [Option B — Docker](#option-b--docker)
  - [Option C — Docker Compose](#option-c--docker-compose)
- [Running](#running)
  - [API server](#api-server)
  - [CLI (no server)](#cli-no-server)
  - [Direct Python import](#direct-python-import)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

---

## Architecture

```
POST /search  {"company": "Stripe"}
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  CrewAI Crew                                          │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │  LinkedIn   │  │  Twitter/X  │  │    Email     │  │
│  │  Agent      │  │  Agent      │  │    Agent     │  │
│  │  Proxycurl  │  │  Twitter    │  │  Hunter.io   │  │
│  │  + Serper   │  │  API v2     │  │  + Apollo    │  │
│  └─────────────┘  └─────────────┘  └──────────────┘  │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   GitHub    │  │    News     │  │  Web Search  │  │
│  │   Agent     │  │   Agent     │  │   Agent      │  │
│  │  GitHub API │  │  NewsAPI    │  │  Serper      │  │
│  │             │  │  + Serper   │  │  + Tavily    │  │
│  └─────────────┘  └─────────────┘  └──────────────┘  │
│                                                       │
│  ┌─────────────┐                                      │
│  │ Enrichment  │  ← Clearbit company + Prospector     │
│  │   Agent     │                                      │
│  └─────────────┘                                      │
│             ↓  all 7 outputs as context               │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Merger Agent  (LLM dedup + JSON synthesis)     │  │
│  └─────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
        │
        ▼
  Deterministic post-processor
  (rapidfuzz token_set_ratio dedup)
        │
        ▼
  {"company": "...", "people": [...]}
```

Each parallel research task hands its output to the LLM Merger Agent, which produces unified JSON. A second deterministic pass with `rapidfuzz` catches any remaining duplicates the LLM missed (middle initials, case differences, word-order variations).

---

## What it collects

Each person record can contain:

| Field | Source |
|---|---|
| Full name | All agents |
| Job title | LinkedIn, Apollo, Clearbit, web |
| Email(s) + confidence | Hunter.io, Apollo, Clearbit, GitHub profile |
| Phone(s) | Apollo, Proxycurl |
| LinkedIn URL | Proxycurl, web search |
| Twitter / X handle | Twitter API, web |
| GitHub username | GitHub API, web |
| Personal website | GitHub profile, web |
| Location | Proxycurl, GitHub, Clearbit |
| Bio / summary | Proxycurl, GitHub, Twitter |
| Source list | Which agents found this person |
| Confidence score | Highest across all sources |

---

## API keys reference

You need **at minimum** one LLM key and one search key. Every other key is optional — agents skip gracefully when their key is absent.

| Env var | Service | Free tier? | Get it |
|---|---|---|---|
| `OPENAI_API_KEY` | GPT-4o (LLM) | No | [platform.openai.com](https://platform.openai.com) |
| `ANTHROPIC_API_KEY` | Claude (LLM) | No | [console.anthropic.com](https://console.anthropic.com) |
| `SERPAPI_API_KEY` | Google/Bing/DDG search | 100 searches/mo free | [serpapi.com](https://serpapi.com) |
| `TAVILY_API_KEY` | AI-optimised search | 1 000 searches/mo free | [tavily.com](https://tavily.com) |
| `PROXYCURL_API_KEY` | LinkedIn profiles & companies | Pay-as-you-go | [nubela.co/proxycurl](https://nubela.co/proxycurl) |
| `TWITTER_BEARER_TOKEN` | Twitter/X API v2 | Free Basic tier | [developer.twitter.com](https://developer.twitter.com) |
| `HUNTER_API_KEY` | Email domain search & finder | 25 searches/mo free | [hunter.io](https://hunter.io) |
| `APOLLO_API_KEY` | People + email + phone | Free tier available | [apollo.io](https://apollo.io) |
| `CLEARBIT_API_KEY` | Company & person enrichment | Free trial | [clearbit.com](https://clearbit.com) |
| `GITHUB_TOKEN` | GitHub org members (raises rate limit) | Free | [github.com/settings/tokens](https://github.com/settings/tokens) |
| `NEWS_API_KEY` | News articles | 100 requests/day free | [newsapi.org](https://newsapi.org) |

> **Tip:** Set `CREW_LLM_MODEL=claude-sonnet-4-6` to use Claude instead of GPT-4o.

---

## Setup

### Prerequisites

- Python 3.10 or later **or** Docker
- At least one LLM API key (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
- At least one search key (`SERPAPI_API_KEY` or `TAVILY_API_KEY`)

---

### Option A — Python virtualenv

```bash
# 1. Clone the repo
git clone https://github.com/baraqai/bossfinder.git
cd bossfinder

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Open .env in your editor and fill in the keys you have
```

---

### Option B — Docker

```bash
# 1. Clone and enter
git clone https://github.com/baraqai/bossfinder.git
cd bossfinder

# 2. Configure keys
cp .env.example .env
# Edit .env

# 3. Build the image
docker build -t bossfinder .

# 4. Run
docker run --env-file .env -p 8000:8000 bossfinder
```

---

### Option C — Docker Compose

```bash
# 1. Clone and enter
git clone https://github.com/baraqai/bossfinder.git
cd bossfinder

# 2. Configure keys
cp .env.example .env
# Edit .env

# 3. Start
docker compose up
```

The service is exposed on `http://localhost:8000`.

---

## Running

### API server

```bash
# After completing any setup option above:
python main.py
# → Server starts on http://0.0.0.0:8000

# Or with uvicorn directly (useful for custom host/port/workers):
uvicorn src.bossfinder.api:app --host 0.0.0.0 --port 8000 --workers 2

# Interactive API docs (Swagger UI):
open http://localhost:8000/docs

# Alternative docs (ReDoc):
open http://localhost:8000/redoc
```

### CLI (no server)

Runs the crew and prints JSON results to stdout — no HTTP server needed.

```bash
python run_cli.py "Stripe"
python run_cli.py "OpenAI"
python run_cli.py "Some Small Startup Inc"
```

### Direct Python import

```python
from dotenv import load_dotenv
load_dotenv()

from src.bossfinder.crew import run_bossfinder

result = run_bossfinder("Stripe")

for person in result.people:
    print(person.name, "|", person.title)
    print("  emails:", person.email)
    print("  linkedin:", person.linkedin_url)
    print("  twitter:", person.twitter_handle)
```

---

## API reference

### `POST /search`

Trigger a full crew search for a company.

**Request**
```json
{ "company": "Stripe" }
```

**Response**
```json
{
  "company": "Stripe",
  "total_found": 24,
  "search_metadata": { "total_unique_people": 24 },
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
      "location": "San Francisco, CA",
      "bio": "...",
      "sources": ["linkedin", "twitter", "web", "github"],
      "confidence": 0.95
    }
  ]
}
```

> **Note:** This is a long-running operation (typically 1–3 minutes) depending on API availability and how many keys are configured.

### `GET /search/{company}`

Convenience alias for `POST /search`.

```bash
curl http://localhost:8000/search/Stripe
```

### `GET /health`

```bash
curl http://localhost:8000/health
# → {"status": "ok", "service": "bossfinder"}
```

---

## Configuration

All configuration is via environment variables (`.env` file or shell env).

| Variable | Default | Description |
|---|---|---|
| `CREW_LLM_MODEL` | `gpt-4o` | LLM model for all agents. Use `claude-sonnet-4-6` for Claude. |
| `HOST` | `0.0.0.0` | API server bind address |
| `PORT` | `8000` | API server port |
| `LOG_LEVEL` | `info` | Uvicorn log level (`debug`, `info`, `warning`, `error`) |

See [`.env.example`](.env.example) for the full list of API key variables.

---

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-new-source
   ```

2. **Add a new agent** — copy one of the existing agents in `src/bossfinder/agents/`, add a matching tool in `src/bossfinder/tools/`, register the agent and task in `src/bossfinder/crew.py`.

3. **Run the tests:**
   ```bash
   pip install -e ".[dev]"
   pytest
   ```

4. **Open a pull request** against `main`. Please include:
   - Which data source you added
   - Which API key(s) are required
   - A sample of the output your agent produces

### Potential contributions

- [ ] AngelList / Wellfound agent
- [ ] Crunchbase API agent
- [ ] Google Maps / Places agent (for office phone numbers)
- [ ] SEC EDGAR filings agent (US public companies)
- [ ] Async/parallel crew execution (reduce wall-clock time)
- [ ] Result caching layer (Redis / SQLite)
- [ ] Webhook support for async results

---

## License

[MIT](LICENSE) © [BaraqAI](https://github.com/baraqai)

---

*Built with [CrewAI](https://crewai.com) · [FastAPI](https://fastapi.tiangolo.com) · [Proxycurl](https://nubela.co/proxycurl) · [Hunter.io](https://hunter.io) · [Apollo.io](https://apollo.io)*
