from crewai import Agent
from crewai_tools import SerperDevTool
from ..tools.news_tool import NewsApiPeopleTool
from ..config import get_settings


def make_news_agent() -> Agent:
    settings = get_settings()
    tools = [NewsApiPeopleTool()]

    if settings.serpapi_api_key:
        tools.append(SerperDevTool())

    return Agent(
        role="News & Press Intelligence Analyst",
        goal=(
            "Find executives and key people at the target company mentioned in news articles, "
            "press releases, and media coverage. Extract names, titles, and any contact "
            "details mentioned in public announcements."
        ),
        backstory=(
            "You track the business press to surface named executives and decision-makers. "
            "News articles, press releases, and interviews often reveal leadership changes, "
            "new hires, and contact details. You synthesise multiple sources to build "
            "a comprehensive picture of a company's key people."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        llm=settings.crew_llm_model,
    )
