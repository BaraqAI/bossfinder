from crewai import Agent
from crewai_tools import SerperDevTool
from ..tools.twitter_tool import TwitterPeopleTool
from ..config import get_settings


def make_twitter_agent() -> Agent:
    settings = get_settings()
    tools = [TwitterPeopleTool()]

    if settings.serpapi_api_key:
        tools.append(SerperDevTool())

    return Agent(
        role="X / Twitter Social Intelligence Analyst",
        goal=(
            "Identify key people at the target company on X (Twitter). "
            "Find their handles, bios, follower counts, and any contact details they share publicly."
        ),
        backstory=(
            "You specialise in social network intelligence gathering. "
            "You search Twitter/X for executives, founders, and notable employees of a company, "
            "analyse their public profiles for contact information, and cross-reference "
            "results with web searches to confirm identities."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        llm=settings.crew_llm_model,
    )
