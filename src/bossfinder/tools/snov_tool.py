import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings

SNOV_BASE = "https://api.snov.io/v1"


def _get_access_token(client_id: str, client_secret: str) -> str | None:
    """Snov uses OAuth2 client-credentials for every request."""
    try:
        resp = httpx.post(
            f"{SNOV_BASE}/oauth/access_token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        pass
    return None


class SnovEmailFinderTool(BaseTool):
    """Find a specific executive's email via Snov.io."""

    name: str = "snov_email_finder"
    description: str = (
        "Find a specific person's professional email using Snov.io. "
        "Input: 'First Last | domain.com' e.g. 'John Smith | acme.com'. "
        "Returns email address and confidence score."
    )
    client_id: str = Field(default="")
    client_secret: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings = get_settings()
        self.client_id = settings.snov_client_id
        self.client_secret = settings.snov_client_secret

    def _run(self, input_str: str) -> str:
        if not self.client_id or not self.client_secret:
            return "SKIP: SNOV_CLIENT_ID / SNOV_CLIENT_SECRET not configured"

        token = _get_access_token(self.client_id, self.client_secret)
        if not token:
            return "Snov.io: could not obtain access token"

        # Parse "First Last | domain.com"
        if "|" in input_str:
            parts = [p.strip() for p in input_str.split("|", 1)]
            name, domain = parts[0], parts[1]
        else:
            tokens = input_str.strip().split()
            domain = tokens[-1] if "." in tokens[-1] else ""
            name = " ".join(tokens[:-1]) if domain else input_str.strip()

        name_parts = name.strip().split()
        first = name_parts[0] if name_parts else ""
        last = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        if not first or not domain:
            return "Provide input as 'First Last | domain.com'"

        try:
            resp = httpx.post(
                f"{SNOV_BASE}/get-emails-from-names",
                json={
                    "access_token": token,
                    "first_name": first,
                    "last_name": last,
                    "domain": domain,
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            emails = data.get("data", {}).get("emails", [])
            if not emails:
                return f"Snov.io: no email found for {name} at {domain}"
            lines = []
            for e in emails:
                address = e.get("email", "")
                confidence = e.get("confidence", "")
                status = e.get("status", "")
                lines.append(f"Email: {address} | Confidence: {confidence} | Status: {status}")
            return "\n".join(lines)
        except Exception as e:
            return f"Snov.io email finder error: {e}"


class SnovDomainSearchTool(BaseTool):
    """Find all known contacts at a company domain via Snov.io."""

    name: str = "snov_domain_search"
    description: str = (
        "Find all known professional contacts at a company using Snov.io domain search. "
        "Input: company domain (e.g. 'acme.com') or company name. "
        "Returns a list of people with name, title, email, and LinkedIn URL."
    )
    client_id: str = Field(default="")
    client_secret: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings = get_settings()
        self.client_id = settings.snov_client_id
        self.client_secret = settings.snov_client_secret

    def _run(self, company: str) -> str:
        if not self.client_id or not self.client_secret:
            return "SKIP: SNOV_CLIENT_ID / SNOV_CLIENT_SECRET not configured"

        token = _get_access_token(self.client_id, self.client_secret)
        if not token:
            return "Snov.io: could not obtain access token"

        domain = company.strip() if "." in company else company.strip()

        try:
            resp = httpx.post(
                f"{SNOV_BASE}/get-domain-emails-with-info",
                json={
                    "access_token": token,
                    "domain": domain,
                    "type": "personal",
                    "limit": 50,
                    "lastId": 0,
                    "position": [
                        "CEO", "CTO", "CFO", "COO", "CMO", "CPO",
                        "Founder", "President", "VP", "Director", "Head",
                    ],
                },
                timeout=25,
            )
            resp.raise_for_status()
            contacts = resp.json().get("data", {}).get("emails", []) or []
            if not contacts:
                return f"No contacts found at domain: {domain}"
            lines = []
            for c in contacts:
                name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
                title = c.get("position", "")
                email = c.get("email", "")
                linkedin = c.get("linkedIn", "") or ""
                lines.append(f"- {name} | {title} | {email} | {linkedin}")
            return "\n".join(lines)
        except Exception as e:
            return f"Snov.io domain search error: {e}"
