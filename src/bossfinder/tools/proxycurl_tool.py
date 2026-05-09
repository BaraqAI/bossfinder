import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings


class ProxycurlCompanyTool(BaseTool):
    """Search LinkedIn company employees via Proxycurl API."""

    name: str = "proxycurl_company_employees"
    description: str = (
        "Fetch employees of a company from LinkedIn using Proxycurl. "
        "Input: company name or LinkedIn company URL. "
        "Returns a list of employees with name, title, LinkedIn URL."
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().proxycurl_api_key

    def _run(self, company: str) -> str:
        if not self.api_key:
            return "SKIP: PROXYCURL_API_KEY not configured"

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # First resolve company LinkedIn URL if plain name given
        company_url = company if "linkedin.com" in company else self._resolve_company_url(company, headers)
        if not company_url:
            return f"Could not resolve LinkedIn URL for: {company}"

        try:
            resp = httpx.get(
                "https://nubela.co/proxycurl/api/linkedin/company/employees/",
                params={"url": company_url, "page_size": 50, "employment_status": "current"},
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            employees = data.get("employees", [])
            lines = []
            for emp in employees:
                profile = emp.get("profile", {})
                name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
                title = profile.get("occupation", "")
                url = emp.get("profile_url", "")
                lines.append(f"- {name} | {title} | {url}")
            return "\n".join(lines) if lines else "No employees found"
        except Exception as e:
            return f"Proxycurl error: {e}"

    def _resolve_company_url(self, name: str, headers: dict) -> str | None:
        try:
            resp = httpx.get(
                "https://nubela.co/proxycurl/api/linkedin/company/resolve",
                params={"company_name": name},
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("url")
        except Exception:
            pass
        return None


class ProxycurlProfileTool(BaseTool):
    """Enrich a single LinkedIn profile via Proxycurl."""

    name: str = "proxycurl_profile_enrich"
    description: str = (
        "Enrich a LinkedIn profile URL to get full contact details. "
        "Input: LinkedIn profile URL. "
        "Returns name, title, email, phone, location, summary."
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().proxycurl_api_key

    def _run(self, linkedin_url: str) -> str:
        if not self.api_key:
            return "SKIP: PROXYCURL_API_KEY not configured"
        try:
            resp = httpx.get(
                "https://nubela.co/proxycurl/api/v2/linkedin",
                params={"url": linkedin_url, "personal_email": "include", "personal_contact_number": "include"},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
            resp.raise_for_status()
            p = resp.json()
            parts = [
                f"Name: {p.get('full_name', '')}",
                f"Title: {p.get('occupation', '')}",
                f"Location: {p.get('city', '')} {p.get('country_full_name', '')}",
                f"Emails: {', '.join(p.get('personal_emails', []))}",
                f"Phones: {', '.join(p.get('personal_numbers', []))}",
                f"Summary: {p.get('summary', '')[:300]}",
            ]
            return "\n".join(parts)
        except Exception as e:
            return f"Proxycurl profile error: {e}"
