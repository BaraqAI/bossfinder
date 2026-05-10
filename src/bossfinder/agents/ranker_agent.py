from crewai import Agent
from ..config import get_settings


def make_ranker_agent() -> Agent:
    settings = get_settings()

    return Agent(
        role="Executive Seniority Ranker",
        goal=(
            "Re-order the merged contact list from most senior to most junior, "
            "based on each person's title and role in the organisation. "
            "C-suite and founders come first, then VPs, then Directors, then Managers, then ICs. "
            "Output the same JSON structure with people sorted by seniority."
        ),
        backstory=(
            "You are an expert in corporate org-chart analysis. "
            "Given a list of people with their titles, you instantly recognise seniority signals: "
            "CEO, founder, CXO, President, SVP, VP, Director, Head of, Manager, Lead, Senior, and IC. "
            "You also add a 'seniority_rank' integer field to each record (1 = most senior) "
            "so downstream consumers can re-sort if needed. "
            "You never drop records or alter contact data — you only reorder and annotate."
        ),
        tools=[],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=settings.crew_llm_model,
    )
