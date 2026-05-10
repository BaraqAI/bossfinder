from crewai import Agent
from crewai_tools import SerperDevTool
from ..tools.hunter_tool import HunterDomainTool, HunterEmailFinderTool
from ..config import get_settings


def make_linkedin_agent() -> Agent:
    settings = get_settings()
    tools = [HunterDomainTool(), HunterEmailFinderTool()]

    # Augment with Serper for LinkedIn-targeted web searches
    if settings.serpapi_api_key:
        tools.append(SerperDevTool())

    return Agent(
        role="LinkedIn Intelligence Specialist",
        goal=(
            "Find every current employee and key executive at the target company on LinkedIn. "
            "Collect full names, job titles, LinkedIn profile URLs, email addresses, and phone numbers."
        ),
        backstory=(
            "You are a specialist in extracting professional intelligence from LinkedIn. "
            "You use Hunter.io to enumerate company employees by domain and find individual email addresses. "
            "When Hunter cannot resolve a profile, you fall back to "
            "targeted Google searches restricted to linkedin.com."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=8,
        llm=settings.crew_llm_model,
    )
