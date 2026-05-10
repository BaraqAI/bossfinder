from crewai import Agent
from ..tools.hunter_tool import HunterDomainTool, HunterEmailFinderTool
from ..tools.apollo_tool import ApolloSearchTool, ApolloEnrichPersonTool
from ..tools.snov_tool import SnovDomainSearchTool, SnovEmailFinderTool
from ..config import get_settings


def make_email_agent() -> Agent:
    settings = get_settings()

    tools = [
        HunterDomainTool(),
        HunterEmailFinderTool(),
        ApolloSearchTool(),
        ApolloEnrichPersonTool(),
        SnovDomainSearchTool(),
        SnovEmailFinderTool(),
    ]

    return Agent(
        role="Email & Contact Discovery Specialist",
        goal=(
            "Find verified email addresses, phone numbers, and LinkedIn URLs for every "
            "senior executive at the target company. "
            "Use Hunter.io, Apollo.io, and Snov.io in combination. "
            "For each named person: try all three sources until an email is confirmed."
        ),
        backstory=(
            "You are a relentless B2B contact hunter with access to three complementary tools. "
            "Your workflow: (1) run Hunter domain search + Snov domain search to get the full "
            "contact list and email pattern; (2) run Apollo executive search to surface senior "
            "people Apollo knows about; (3) for every named executive found — regardless of source — "
            "call apollo_enrich_person, hunter_email_finder, and snov_email_finder in turn until "
            "you have a confirmed email. Never give up on a name after just one tool fails. "
            "Record confidence scores and flag unverified addresses."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        llm=settings.crew_llm_model,
    )
