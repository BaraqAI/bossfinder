import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings


class HunterDomainTool(BaseTool):
    """Find email addresses at a company domain via Hunter.io."""

    name: str = "hunter_domain_search"
    description: str = (
        "Find professional email addresses at a company using Hunter.io. "
        "Input: company name or domain (e.g. 'acme.com' or 'Acme Corp'). "
        "Returns a list of people with name, email, title, confidence score."
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().hunter_api_key

    def _run(self, company: str) -> str:
        if not self.api_key:
            return "SKIP: HUNTER_API_KEY not configured"

        # Hunter works better with domains; try to guess domain from name
        domain = company if "." in company else None

        try:
            params: dict = {"api_key": self.api_key, "limit": 10}
            if domain:
                params["domain"] = domain
            else:
                params["company"] = company

            resp = httpx.get(
                "https://api.hunter.io/v2/domain-search",
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            emails = data.get("emails", [])
            lines = []
            for entry in emails:
                name = f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip()
                email = entry.get("value", "")
                title = entry.get("position", "")
                confidence = entry.get("confidence", 0)
                lines.append(f"- {name} | {title} | {email} | confidence:{confidence}%")

            domain_info = data.get("domain", company)
            header = f"Domain: {domain_info} | Pattern: {data.get('pattern', 'unknown')}\n"
            return header + ("\n".join(lines) if lines else "No emails found")
        except Exception as e:
            return f"Hunter.io error: {e}"


class HunterCompanyEnrichTool(BaseTool):
    """Enrich company data and find key contacts via Hunter.io."""

    name: str = "hunter_company_enrich"
    description: str = (
        "Enrich company information using Hunter.io. "
        "Input: company domain (e.g. 'stripe.com') or company name. "
        "Returns industry, description, LinkedIn/Twitter handles, employee count, and top contacts."
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().hunter_api_key

    def _run(self, company: str) -> str:
        if not self.api_key:
            return "SKIP: HUNTER_API_KEY not configured"

        domain = company.strip() if "." in company else self._resolve_domain(company)
        if not domain:
            return f"Could not resolve domain for: {company}"

        try:
            resp = httpx.get(
                "https://api.hunter.io/v2/companies/find",
                params={"domain": domain, "api_key": self.api_key},
                timeout=20,
            )
            if resp.status_code == 404:
                return f"No company found for: {domain}"
            resp.raise_for_status()
            c = resp.json().get("data", {})

            twitter = c.get("twitter", "")
            if twitter and not twitter.startswith("@"):
                twitter = f"@{twitter}"

            lines = [
                f"Company: {c.get('name', '')}",
                f"Domain: {domain}",
                f"Industry: {c.get('industry', '')}",
                f"Employees: {c.get('size', '')}",
                f"Description: {(c.get('description') or '')[:250]}",
                f"LinkedIn: {c.get('linkedin', '')}",
                f"Twitter: {twitter}",
                f"Location: {', '.join(filter(None, [c.get('city', ''), c.get('country', '')]))}",
                f"Phone: {c.get('phone', '')}",
                "",
                "Key contacts:",
            ]

            # Pull top contacts via domain search
            contacts_resp = httpx.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "limit": 20, "api_key": self.api_key},
                timeout=20,
            )
            if contacts_resp.status_code == 200:
                for e in contacts_resp.json().get("data", {}).get("emails", []):
                    name = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
                    title = e.get("position", "")
                    email = e.get("value", "")
                    lines.append(f"- {name} | {title} | {email}")

            return "\n".join(lines)
        except Exception as e:
            return f"Hunter company enrich error: {e}"

    def _resolve_domain(self, company_name: str) -> str | None:
        try:
            resp = httpx.get(
                "https://api.hunter.io/v2/domains/find",
                params={"company": company_name, "api_key": self.api_key},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json().get("data", {}).get("domain")
        except Exception:
            pass
        return None


class HunterEmailFinderTool(BaseTool):
    """Find a specific person's email via Hunter.io email finder."""

    name: str = "hunter_email_finder"
    description: str = (
        "Find the email address of a specific person at a company. "
        "Input: JSON string with keys 'full_name' and 'company' or 'domain'. "
        "Example: '{\"full_name\": \"John Smith\", \"domain\": \"acme.com\"}'"
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().hunter_api_key

    def _run(self, query: str) -> str:
        if not self.api_key:
            return "SKIP: HUNTER_API_KEY not configured"

        import json
        try:
            data = json.loads(query)
        except Exception:
            return "Input must be valid JSON: {\"full_name\": \"...\", \"domain\": \"...\"}"

        name = data.get("full_name", "")
        parts = name.split(" ", 1)
        first = parts[0] if parts else ""
        last = parts[1] if len(parts) > 1 else ""

        params = {
            "api_key": self.api_key,
            "first_name": first,
            "last_name": last,
        }
        if "domain" in data:
            params["domain"] = data["domain"]
        elif "company" in data:
            params["company"] = data["company"]

        try:
            resp = httpx.get("https://api.hunter.io/v2/email-finder", params=params, timeout=15)
            resp.raise_for_status()
            result = resp.json().get("data", {})
            email = result.get("email", "")
            score = result.get("score", 0)
            return f"Email: {email} | Confidence: {score}%" if email else "Email not found"
        except Exception as e:
            return f"Hunter email finder error: {e}"
