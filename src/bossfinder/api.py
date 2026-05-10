"""
BossFinder FastAPI application.

POST /search  { "company": "Stripe" }
  → triggers the full crew, returns merged contact list
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import get_settings
from .crew import run_bossfinder
from .models.person import CompanySearchResult

logger = logging.getLogger("bossfinder.api")

# Thread pool: CrewAI is synchronous; we run it in a thread to keep the event loop free
_executor = ThreadPoolExecutor(max_workers=4)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("BossFinder starting — model: %s", settings.crew_llm_model)
    yield
    _executor.shutdown(wait=False)


app = FastAPI(
    title="BossFinder",
    description=(
        "Multi-agent company intelligence API. "
        "Given a company name it searches LinkedIn, GitHub, Hunter.io, "
        "NewsAPI, and the open web to find key people and contacts."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class SearchRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200, description="Company name to research")


class PersonResponse(BaseModel):
    name: str
    title: str | None = None
    company: str | None = None
    email: list[str] = []
    phone: list[str] = []
    linkedin_url: str | None = None
    twitter_handle: str | None = None
    github_username: str | None = None
    website: str | None = None
    location: str | None = None
    bio: str | None = None
    sources: list[str] = []
    confidence: float = 0.0
    seniority_rank: int | None = None


class SearchResponse(BaseModel):
    company: str
    people: list[PersonResponse]
    total_found: int
    search_metadata: dict[str, Any] = {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "bossfinder"}


@app.post("/search", response_model=SearchResponse)
async def search_company(request: SearchRequest) -> SearchResponse:
    """
    Trigger the BossFinder crew for the given company name.
    Returns a deduplicated list of key people and all available contact channels.

    This is a long-running operation (typically 1–3 minutes depending on API availability).
    """
    company = request.company.strip()
    if not company:
        raise HTTPException(status_code=400, detail="company name cannot be empty")

    logger.info("Starting BossFinder search for: %s", company)

    try:
        loop = asyncio.get_event_loop()
        result: CompanySearchResult = await loop.run_in_executor(
            _executor,
            run_bossfinder,
            company,
        )
    except Exception as exc:
        logger.exception("BossFinder crew failed for %s", company)
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

    people_out = [
        PersonResponse(
            name=p.name,
            title=p.title,
            company=p.company or company,
            email=p.email,
            phone=p.phone,
            linkedin_url=p.linkedin_url,
            twitter_handle=p.twitter_handle,
            github_username=p.github_username,
            website=p.website,
            location=p.location,
            bio=p.bio,
            sources=p.sources,
            confidence=round(p.confidence, 3),
            seniority_rank=p.seniority_rank,
        )
        for p in result.people
    ]

    return SearchResponse(
        company=result.company,
        people=people_out,
        total_found=len(people_out),
        search_metadata=result.search_metadata,
    )


@app.get("/search/{company}", response_model=SearchResponse)
async def search_company_get(company: str) -> SearchResponse:
    """Convenience GET endpoint — same as POST /search."""
    return await search_company(SearchRequest(company=company))
