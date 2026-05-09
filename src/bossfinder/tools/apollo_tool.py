import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings


class ApolloSearchTool(BaseTool):
    """Search Apollo.io for people at a company (email + phone + LinkedIn)."""

    name: str = "apollo_people_search"
    description: str = (
        "Search Apollo.io for key people at a company. "
        "Returns name, title, email, phone, LinkedIn URL. "
        "Input: company name."
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().apollo_api_key

    def _run(self, company: str) -> str:
        if not self.api_key:
            return "SKIP: APOLLO_API_KEY not configured"

        try:
            resp = httpx.post(
                "https://api.apollo.io/api/v1/mixed_people/search",
                json={
                    "api_key": self.api_key,
                    "q_organization_name": company,
                    "page": 1,
                    "per_page": 25,
                    "person_titles": [
                        "CEO", "CTO", "CFO", "COO", "CMO", "CPO",
                        "founder", "co-founder", "president", "VP", "director", "head of",
                    ],
                },
                timeout=30,
            )
            resp.raise_for_status()
            people = resp.json().get("people", [])
            lines = []
            for p in people:
                name = p.get("name", "")
                title = p.get("title", "")
                email = p.get("email", "")
                phone = (p.get("phone_numbers") or [{}])[0].get("sanitized_number", "")
                linkedin = p.get("linkedin_url", "")
                lines.append(f"- {name} | {title} | email:{email} | phone:{phone} | {linkedin}")
            return "\n".join(lines) if lines else "No results from Apollo"
        except Exception as e:
            return f"Apollo error: {e}"
