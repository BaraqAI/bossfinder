import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings

APOLLO_BASE = "https://api.apollo.io/api/v1"

EXEC_TITLES = [
    "CEO", "CTO", "CFO", "COO", "CMO", "CPO", "CISO", "CRO", "CLO",
    "founder", "co-founder", "president", "executive chairman",
    "SVP", "EVP", "senior vice president", "executive vice president",
    "VP", "vice president", "general manager", "managing director",
    "director", "head of",
]


class ApolloSearchTool(BaseTool):
    """Search Apollo.io for senior executives at a company."""

    name: str = "apollo_people_search"
    description: str = (
        "Search Apollo.io for senior executives at a company. "
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
                f"{APOLLO_BASE}/mixed_people/search",
                json={
                    "api_key": self.api_key,
                    "q_organization_name": company,
                    "page": 1,
                    "per_page": 25,
                    "person_titles": EXEC_TITLES,
                    "person_seniority": ["owner", "founder", "c_suite", "vp", "director"],
                },
                timeout=30,
            )
            resp.raise_for_status()
            people = resp.json().get("people", [])
            if not people:
                return "No results from Apollo"
            lines = []
            for p in people:
                lines.append(_format_person(p))
            return "\n".join(lines)
        except Exception as e:
            return f"Apollo search error: {e}"


class ApolloEnrichPersonTool(BaseTool):
    """Enrich a specific named person via Apollo.io to reveal their email and phone."""

    name: str = "apollo_enrich_person"
    description: str = (
        "Enrich a specific named executive via Apollo.io to get their verified email and phone. "
        "Input: 'Name | Company' e.g. 'John Smith | Acme Corp' or just 'John Smith Acme Corp'. "
        "Returns email, phone, LinkedIn URL, and title."
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().apollo_api_key

    def _run(self, input_str: str) -> str:
        if not self.api_key:
            return "SKIP: APOLLO_API_KEY not configured"

        # Parse "Name | Company" or "Name Company"
        if "|" in input_str:
            parts = [p.strip() for p in input_str.split("|", 1)]
            name, company = parts[0], parts[1] if len(parts) > 1 else ""
        else:
            tokens = input_str.strip().split()
            # Heuristic: last capitalised word(s) = company if >2 tokens
            name = input_str.strip()
            company = ""

        name_parts = name.strip().split()
        first = name_parts[0] if name_parts else ""
        last = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        try:
            # Step 1: search to get the person's Apollo ID
            search_payload: dict = {
                "api_key": self.api_key,
                "q_person_name": name.strip(),
                "page": 1,
                "per_page": 5,
            }
            if company:
                search_payload["q_organization_name"] = company

            search_resp = httpx.post(
                f"{APOLLO_BASE}/mixed_people/search",
                json=search_payload,
                timeout=20,
            )
            search_resp.raise_for_status()
            people = search_resp.json().get("people", [])
            if not people:
                return f"Apollo: no match found for '{name}'"

            person = people[0]
            person_id = person.get("id", "")

            # Step 2: reveal/enrich to get email + phone (costs a credit)
            if person_id:
                enrich_resp = httpx.post(
                    f"{APOLLO_BASE}/people/match",
                    json={
                        "api_key": self.api_key,
                        "id": person_id,
                        "first_name": first,
                        "last_name": last,
                        "organization_name": company,
                        "reveal_personal_emails": True,
                    },
                    timeout=20,
                )
                if enrich_resp.status_code == 200:
                    person = enrich_resp.json().get("person", person)

            return _format_person(person)
        except Exception as e:
            return f"Apollo enrich error: {e}"


def _format_person(p: dict) -> str:
    name = p.get("name", "")
    title = p.get("title", "")
    email = p.get("email", "") or ""
    phones = p.get("phone_numbers") or []
    phone = phones[0].get("sanitized_number", "") if phones else ""
    linkedin = p.get("linkedin_url", "") or ""
    org = p.get("organization", {}) or {}
    company = org.get("name", "") if isinstance(org, dict) else ""
    return f"- {name} | {title} | {company} | email:{email} | phone:{phone} | {linkedin}"
