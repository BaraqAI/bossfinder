from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    crew_llm_model: str = Field(default="gpt-4o", alias="CREW_LLM_MODEL")

    # Search
    serpapi_api_key: str = Field(default="", alias="SERPAPI_API_KEY")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    # Twitter / X
    twitter_bearer_token: str = Field(default="", alias="TWITTER_BEARER_TOKEN")
    twitter_api_key: str = Field(default="", alias="TWITTER_API_KEY")
    twitter_api_secret: str = Field(default="", alias="TWITTER_API_SECRET")
    twitter_access_token: str = Field(default="", alias="TWITTER_ACCESS_TOKEN")
    twitter_access_token_secret: str = Field(default="", alias="TWITTER_ACCESS_TOKEN_SECRET")

    # Email & contact discovery
    hunter_api_key: str = Field(default="", alias="HUNTER_API_KEY")
    apollo_api_key: str = Field(default="", alias="APOLLO_API_KEY")
    snov_client_id: str = Field(default="", alias="SNOV_CLIENT_ID")
    snov_client_secret: str = Field(default="", alias="SNOV_CLIENT_SECRET")


    # GitHub
    github_token: str = Field(default="", alias="GITHUB_TOKEN")

    # News
    news_api_key: str = Field(default="", alias="NEWS_API_KEY")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
