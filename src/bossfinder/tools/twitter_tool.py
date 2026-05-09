import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings


class TwitterPeopleTool(BaseTool):
    """Search Twitter/X for people associated with a company."""

    name: str = "twitter_company_people"
    description: str = (
        "Search Twitter/X for people who work at or are associated with a company. "
        "Input: company name. "
        "Returns Twitter handles, names, bios, and follower counts."
    )
    bearer_token: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bearer_token = get_settings().twitter_bearer_token

    def _run(self, company: str) -> str:
        if not self.bearer_token:
            return "SKIP: TWITTER_BEARER_TOKEN not configured"

        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        results = []

        # Search for people mentioning the company in their bio
        queries = [
            f'"{company}" (CEO OR CTO OR founder OR director OR VP OR president) -is:retweet',
            f'"works at {company}" OR "at {company}" -is:retweet',
        ]

        try:
            for query in queries:
                resp = httpx.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    params={
                        "query": query,
                        "max_results": 10,
                        "expansions": "author_id",
                        "user.fields": "name,username,description,location,public_metrics,url",
                    },
                    headers=headers,
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
                    for user in users.values():
                        metrics = user.get("public_metrics", {})
                        results.append(
                            f"- @{user['username']} | {user['name']} | "
                            f"followers:{metrics.get('followers_count', 0)} | "
                            f"bio:{user.get('description', '')[:150]}"
                        )

            # Also search for the company account and extract employees from lists
            company_user = self._find_company_account(company, headers)
            if company_user:
                results.insert(0, f"[Company account] @{company_user}")

            return "\n".join(results) if results else "No Twitter results found"
        except Exception as e:
            return f"Twitter search error: {e}"

    def _find_company_account(self, company: str, headers: dict) -> str | None:
        try:
            resp = httpx.get(
                "https://api.twitter.com/2/users/by",
                params={"usernames": company.lower().replace(" ", ""), "user.fields": "name,description"},
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    return data[0]["username"]
        except Exception:
            pass
        return None
