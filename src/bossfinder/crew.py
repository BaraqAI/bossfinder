"""
BossFinder Crew – orchestrates all research agents in parallel then merges results.
"""

import os
from crewai import Crew, Process

from .agents.linkedin_agent import make_linkedin_agent
from .agents.twitter_agent import make_twitter_agent
from .agents.email_agent import make_email_agent
from .agents.github_agent import make_github_agent
from .agents.news_agent import make_news_agent
from .agents.web_search_agent import make_web_search_agent, make_hunter_enrichment_agent
from .agents.merger_agent import make_merger_agent
from .agents.ranker_agent import make_ranker_agent

from .tasks.search_tasks import (
    make_linkedin_task,
    make_twitter_task,
    make_email_task,
    make_github_task,
    make_news_task,
    make_web_search_task,
    make_enrichment_task,
    make_merger_task,
    make_ranker_task,
)

from .config import get_settings
from .merger import parse_agent_output, merge_results
from .models.person import CompanySearchResult


def _wire_env() -> None:
    """Ensure crewai and crewai-tools see the right env vars."""
    settings = get_settings()
    if settings.serpapi_api_key:
        os.environ.setdefault("SERPER_API_KEY", settings.serpapi_api_key)
    if settings.tavily_api_key:
        os.environ.setdefault("TAVILY_API_KEY", settings.tavily_api_key)
    if settings.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    if settings.anthropic_api_key:
        os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)


def run_bossfinder(company: str) -> CompanySearchResult:
    """
    Execute the full BossFinder crew for the given company name.
    Returns a merged, deduplicated CompanySearchResult.
    """
    _wire_env()

    # ── Agents ────────────────────────────────────────────────────────────────
    linkedin_agent = make_linkedin_agent()
    # twitter_agent = make_twitter_agent()  # excluded from pipeline for now
    email_agent = make_email_agent()
    github_agent = make_github_agent()
    news_agent = make_news_agent()
    web_agent = make_web_search_agent()
    enrichment_agent = make_hunter_enrichment_agent()
    merger_agent = make_merger_agent()
    ranker_agent = make_ranker_agent()

    # ── Parallel research tasks ───────────────────────────────────────────────
    linkedin_task = make_linkedin_task(linkedin_agent, company)
    # twitter_task = make_twitter_task(twitter_agent, company)  # excluded from pipeline for now
    email_task = make_email_task(email_agent, company)
    github_task = make_github_task(github_agent, company)
    news_task = make_news_task(news_agent, company)
    web_task = make_web_search_task(web_agent, company)
    enrichment_task = make_enrichment_task(enrichment_agent, company)

    research_tasks = [
        linkedin_task,
        email_task,
        github_task,
        news_task,
        web_task,
        enrichment_task,
    ]

    # ── Merger task gets all research task outputs as context ─────────────────
    merger_task = make_merger_task(merger_agent, company)
    merger_task.context = research_tasks

    # ── Ranker task gets the merger output as context ─────────────────────────
    ranker_task = make_ranker_task(ranker_agent, company)
    ranker_task.context = [merger_task]

    all_tasks = research_tasks + [merger_task, ranker_task]
    all_agents = [
        linkedin_agent,
        email_agent,
        github_agent,
        news_agent,
        web_agent,
        enrichment_agent,
        merger_agent,
        ranker_agent,
    ]

    # ── Crew: research tasks run in parallel, merger runs sequentially after ──
    crew = Crew(
        agents=all_agents,
        tasks=all_tasks,
        process=Process.sequential,  # merger must wait; parallel for research below
        verbose=True,
    )

    result = crew.kickoff(inputs={"company": company})

    # ── Post-process: deterministic dedup + seniority sort on top of LLM output ─
    # crew.kickoff returns the last task's output — that's the ranker's JSON
    ranker_output = str(result)

    # Parse all individual research task outputs for completeness
    all_people = []
    source_map = {
        linkedin_task: "linkedin",
        email_task: "email",
        github_task: "github",
        news_task: "news",
        web_task: "web",
        enrichment_task: "hunter",
    }
    for task, source in source_map.items():
        if hasattr(task, "output") and task.output:
            all_people.extend(parse_agent_output(str(task.output), source))

    # Parse the merger output as well
    if hasattr(merger_task, "output") and merger_task.output:
        all_people.extend(parse_agent_output(str(merger_task.output), "merged"))

    # Parse the ranker output — it is authoritative for order and seniority_rank
    ranked_people = parse_agent_output(ranker_output, "ranked")

    # If the ranker produced a valid ranked list, use it as the seed for merge_results
    # so the deterministic dedup pass inherits its seniority_rank annotations
    seed = ranked_people if ranked_people else all_people
    all_people_combined = seed + [p for p in all_people if p not in seed]

    return merge_results(all_people_combined, company)
