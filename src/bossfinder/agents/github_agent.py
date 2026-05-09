from crewai import Agent
from ..tools.github_tool import GitHubOrgMembersTool
from ..config import get_settings


def make_github_agent() -> Agent:
    settings = get_settings()

    return Agent(
        role="GitHub Engineering Intelligence Specialist",
        goal=(
            "Find the technical team and key engineers at the target company via GitHub. "
            "Extract public emails, GitHub usernames, personal websites, and bios from "
            "organization members and prominent contributors."
        ),
        backstory=(
            "You are a technical intelligence specialist who mines GitHub organizations "
            "for engineering team information. Many developers publicly list their work email "
            "and social links on their GitHub profile. You enumerate org members and enrich "
            "each profile to extract every available contact channel."
        ),
        tools=[GitHubOrgMembersTool()],
        verbose=True,
        allow_delegation=False,
        llm=settings.crew_llm_model,
    )
