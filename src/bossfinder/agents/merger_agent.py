from crewai import Agent
from ..config import get_settings


def make_merger_agent() -> Agent:
    settings = get_settings()

    return Agent(
        role="Contact Data Aggregator & Deduplicator",
        goal=(
            "Aggregate all findings from every research agent into a single, "
            "clean, deduplicated list of key people and their contacts. "
            "Merge duplicate records for the same person. "
            "Output a structured JSON list."
        ),
        backstory=(
            "You are a data quality specialist. You receive raw, overlapping results "
            "from multiple research agents and synthesise them into a unified contact list. "
            "You detect when two records refer to the same person (same name, similar title, "
            "same company), merge their contact details, deduplicate emails and phones, "
            "and assign a confidence score to each final record. "
            "You always output valid JSON."
        ),
        tools=[],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=settings.crew_llm_model,
    )
