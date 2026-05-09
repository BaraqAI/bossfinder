from crewai import Agent
from ..tools.hunter_tool import HunterDomainTool, HunterEmailFinderTool
from ..tools.apollo_tool import ApolloSearchTool
from ..config import get_settings


def make_email_agent() -> Agent:
    settings = get_settings()

    return Agent(
        role="Email & Contact Discovery Specialist",
        goal=(
            "Discover verified email addresses and phone numbers for all key people "
            "at the target company using Hunter.io and Apollo.io. "
            "Provide confidence scores for each contact found."
        ),
        backstory=(
            "You are an expert in B2B contact discovery. "
            "You leverage Hunter.io domain search to uncover the email pattern and all known "
            "addresses at a company, then use the Hunter email finder and Apollo.io to pinpoint "
            "contacts for specific individuals. You always note confidence levels and flag "
            "unverified data."
        ),
        tools=[HunterDomainTool(), HunterEmailFinderTool(), ApolloSearchTool()],
        verbose=True,
        allow_delegation=False,
        llm=settings.crew_llm_model,
    )
