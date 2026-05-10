from pydantic import BaseModel, Field
from typing import Optional


class PersonContact(BaseModel):
    name: str
    title: Optional[str] = None
    company: Optional[str] = None

    # Contact channels
    email: list[str] = Field(default_factory=list)
    phone: list[str] = Field(default_factory=list)
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    github_username: Optional[str] = None
    website: Optional[str] = None

    # Meta
    location: Optional[str] = None
    bio: Optional[str] = None
    sources: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    seniority_rank: Optional[int] = None

    def merge(self, other: "PersonContact") -> "PersonContact":
        """Merge another record into this one, keeping the richest data."""
        merged = self.model_copy(deep=True)

        if not merged.title and other.title:
            merged.title = other.title
        if not merged.company and other.company:
            merged.company = other.company
        if not merged.linkedin_url and other.linkedin_url:
            merged.linkedin_url = other.linkedin_url
        if not merged.twitter_handle and other.twitter_handle:
            merged.twitter_handle = other.twitter_handle
        if not merged.github_username and other.github_username:
            merged.github_username = other.github_username
        if not merged.website and other.website:
            merged.website = other.website
        if not merged.location and other.location:
            merged.location = other.location
        if not merged.bio and other.bio:
            merged.bio = other.bio

        for email in other.email:
            if email and email not in merged.email:
                merged.email.append(email)
        for phone in other.phone:
            if phone and phone not in merged.phone:
                merged.phone.append(phone)
        for source in other.sources:
            if source not in merged.sources:
                merged.sources.append(source)

        merged.confidence = max(merged.confidence, other.confidence)
        return merged


class CompanySearchResult(BaseModel):
    company: str
    people: list[PersonContact] = Field(default_factory=list)
    search_metadata: dict = Field(default_factory=dict)
