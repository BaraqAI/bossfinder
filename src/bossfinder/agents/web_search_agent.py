from crewai import Agent
from crewai_tools import SerperDevTool
from ..config import get_settings

try:
    from crewai_tools import TavilySearchTool as _TavilySearchTool
except ImportError:
    _TavilySearchTool = None


def make_web_search_agent() -> Agent:
    settings = get_settings()
    tools = []

    if settings.serpapi_api_key:
        tools.append(SerperDevTool())
    if settings.tavily_api_key and _TavilySearchTool is not None:
        tools.append(_TavilySearchTool())

    # Always include DuckDuckGo as a free fallback
    try:
        from crewai_tools import DuckDuckGoSearchRun
        tools.append(DuckDuckGoSearchRun())
    except ImportError:
        pass

    return Agent(
        role="General Web Intelligence Researcher",
        goal=(
            "Perform broad web searches to find key people, executives, founders, and "
            "notable employees at the target company. "
            "Search across all public web sources: company websites, interview sites, "
            "conference speaker lists, about pages, and directory sites. "
            "Collect names, titles, emails, social handles, and personal websites."
        ),
        backstory=(
            "You are a seasoned open-source intelligence (OSINT) researcher. "
            "You know that key people appear on company 'About' pages, conference speaker bios, "
            "Crunchbase, AngelList, Product Hunt, podcast guest lists, and interview sites. "
            "You craft precise search queries to surface these contacts efficiently and "
            "cross-reference findings across multiple sources for accuracy."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        llm=settings.crew_llm_model,
    )


def make_hunter_enrichment_agent() -> Agent:
    settings = get_settings()
    tools = []

    if settings.serpapi_api_key:
        tools.append(SerperDevTool())

    try:
        from ..tools.hunter_tool import HunterCompanyEnrichTool
        tools.append(HunterCompanyEnrichTool())
    except Exception:
        pass

    return Agent(
        role="Company & People Enrichment Specialist",
        goal=(
            "Enrich the company profile and find executive contacts via Hunter.io. "
            "Determine the company domain, industry, size, LinkedIn and Twitter handles, "
            "and a complete list of known executive contacts."
        ),
        backstory=(
            "You specialise in B2B data enrichment. You use Hunter.io to pull structured "
            "company and people data, filling gaps that raw web searches miss. "
            "You resolve company names to domains and map domains to executive email addresses."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        llm=settings.crew_llm_model,
    )
