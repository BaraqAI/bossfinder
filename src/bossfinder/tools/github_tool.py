import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings


class GitHubOrgMembersTool(BaseTool):
    """Find public GitHub org members and their contact info."""

    name: str = "github_org_members"
    description: str = (
        "Find public GitHub organization members for a company. "
        "Returns GitHub usernames, names, emails, bios, and blog URLs. "
        "Input: company name or GitHub org name."
    )
    token: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.token = get_settings().github_token

    def _run(self, company: str) -> str:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # Try to find org by name
        org_slug = company.lower().replace(" ", "-").replace(".", "")
        lines = []

        try:
            # Search for org
            search_resp = httpx.get(
                "https://api.github.com/search/users",
                params={"q": f"{company} type:org", "per_page": 5},
                headers=headers,
                timeout=15,
            )
            orgs = search_resp.json().get("items", []) if search_resp.status_code == 200 else []

            # Also try exact slug
            exact_resp = httpx.get(f"https://api.github.com/orgs/{org_slug}", headers=headers, timeout=10)
            if exact_resp.status_code == 200:
                orgs.insert(0, exact_resp.json())

            for org in orgs[:2]:
                org_login = org.get("login", "")
                members_resp = httpx.get(
                    f"https://api.github.com/orgs/{org_login}/public_members",
                    params={"per_page": 30},
                    headers=headers,
                    timeout=15,
                )
                if members_resp.status_code != 200:
                    continue
                for member in members_resp.json():
                    user_resp = httpx.get(
                        f"https://api.github.com/users/{member['login']}",
                        headers=headers,
                        timeout=10,
                    )
                    if user_resp.status_code == 200:
                        u = user_resp.json()
                        lines.append(
                            f"- {u.get('name', member['login'])} | @{u.get('login')} | "
                            f"email:{u.get('email', '')} | blog:{u.get('blog', '')} | "
                            f"bio:{(u.get('bio') or '')[:120]}"
                        )

            return "\n".join(lines) if lines else f"No public GitHub org found for: {company}"
        except Exception as e:
            return f"GitHub error: {e}"
