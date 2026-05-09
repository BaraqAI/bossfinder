import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings


class ClearbitCompanyTool(BaseTool):
    """Enrich company data and find key contacts via Clearbit."""

    name: str = "clearbit_company_enrich"
    description: str = (
        "Enrich company information and find executives via Clearbit. "
        "Input: company domain (e.g. 'stripe.com') or company name. "
        "Returns company info, employee count, and executive contacts."
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().clearbit_api_key

    def _run(self, company: str) -> str:
        if not self.api_key:
            return "SKIP: CLEARBIT_API_KEY not configured"

        domain = company if "." in company else None
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            if not domain:
                # Resolve domain via Clearbit Autocomplete
                resp = httpx.get(
                    "https://autocomplete.clearbit.com/v1/companies/suggest",
                    params={"query": company},
                    timeout=10,
                )
                if resp.status_code == 200 and resp.json():
                    domain = resp.json()[0].get("domain", "")

            if not domain:
                return f"Could not resolve domain for: {company}"

            resp = httpx.get(
                f"https://company.clearbit.com/v2/companies/find",
                params={"domain": domain},
                headers=headers,
                timeout=20,
            )
            resp.raise_for_status()
            c = resp.json()

            lines = [
                f"Company: {c.get('name', '')}",
                f"Domain: {domain}",
                f"Type: {c.get('type', '')}",
                f"Employees: {c.get('metrics', {}).get('employees', '')}",
                f"Description: {(c.get('description') or '')[:200]}",
                f"LinkedIn: {c.get('linkedin', {}).get('handle', '')}",
                f"Twitter: @{c.get('twitter', {}).get('handle', '')}",
                f"Phone: {c.get('phone', '')}",
                "",
                "Key contacts from Clearbit Reveal:",
            ]

            # Fetch people via Clearbit Prospector if available
            people_resp = httpx.get(
                "https://prospector.clearbit.com/v1/people/search",
                params={"domain": domain, "role": "executive", "limit": 20},
                headers=headers,
                timeout=20,
            )
            if people_resp.status_code == 200:
                for p in people_resp.json().get("results", []):
                    name = p.get("name", {})
                    full_name = f"{name.get('fullName', '')}"
                    title = p.get("title", "")
                    email = p.get("email", "")
                    linkedin = p.get("linkedin", {}).get("handle", "")
                    lines.append(f"- {full_name} | {title} | {email} | linkedin:{linkedin}")

            return "\n".join(lines)
        except Exception as e:
            return f"Clearbit error: {e}"
