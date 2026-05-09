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
            params: dict = {"api_key": self.api_key, "limit": 50}
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
