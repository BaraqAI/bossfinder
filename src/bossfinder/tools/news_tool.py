import httpx
from crewai.tools import BaseTool
from pydantic import Field
from ..config import get_settings


class NewsApiPeopleTool(BaseTool):
    """Search news articles to extract named executives at a company."""

    name: str = "news_company_executives"
    description: str = (
        "Search recent news articles to find executives and key people mentioned at a company. "
        "Input: company name. "
        "Returns article titles and snippets mentioning key people."
    )
    api_key: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = get_settings().news_api_key

    def _run(self, company: str) -> str:
        if not self.api_key:
            return "SKIP: NEWS_API_KEY not configured"

        queries = [
            f'"{company}" CEO',
            f'"{company}" founder',
            f'"{company}" executive appointment',
        ]

        lines = []
        seen_titles: set[str] = set()

        try:
            for q in queries:
                resp = httpx.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": q,
                        "apiKey": self.api_key,
                        "pageSize": 5,
                        "sortBy": "relevancy",
                        "language": "en",
                    },
                    timeout=15,
                )
                if resp.status_code != 200:
                    continue
                for article in resp.json().get("articles", []):
                    title = article.get("title", "")
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    description = article.get("description", "")
                    source = article.get("source", {}).get("name", "")
                    url = article.get("url", "")
                    lines.append(f"[{source}] {title}\n  {description}\n  {url}")

            return "\n\n".join(lines) if lines else "No news results found"
        except Exception as e:
            return f"NewsAPI error: {e}"
