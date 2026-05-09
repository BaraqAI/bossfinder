from crewai import Agent
from crewai_tools import SerperDevTool
from ..tools.proxycurl_tool import ProxycurlCompanyTool, ProxycurlProfileTool
from ..config import get_settings


def make_linkedin_agent() -> Agent:
    settings = get_settings()
    tools = [ProxycurlCompanyTool(), ProxycurlProfileTool()]

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
            "You use the Proxycurl API to enumerate company employees and enrich each profile "
            "with contact details. When Proxycurl cannot resolve a profile, you fall back to "
            "targeted Google searches restricted to linkedin.com."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        llm=settings.crew_llm_model,
    )
