from crewai import Task
from crewai import Agent


PERSON_JSON_SCHEMA = """
{
  "people": [
    {
      "name": "string",
      "title": "string",
      "company": "string",
      "email": ["string"],
      "phone": ["string"],
      "linkedin_url": "string",
      "twitter_handle": "string",
      "github_username": "string",
      "website": "string",
      "location": "string",
      "bio": "string",
      "sources": ["string"],
      "confidence": 0.0
    }
  ]
}
"""


def make_linkedin_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Search LinkedIn for current employees and key executives at '{company}'. "
            "Use Proxycurl to enumerate company employees and enrich the top 20 profiles "
            "to collect emails and phone numbers. "
            "For any profiles Proxycurl cannot enrich, run a site:linkedin.com Google search "
            "to find their profile URL, then enrich it. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array. Each person must include at minimum: "
            "name, title, linkedin_url, and any available email/phone. Source should be 'linkedin'."
        ),
        agent=agent,
    )


def make_twitter_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Search Twitter/X for people who work at or are executives of '{company}'. "
            "Find their Twitter handles, real names, bios, and any contact info they share publicly. "
            "Also identify the official company Twitter account. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array. Each person must include: "
            "name, twitter_handle, title (if visible in bio), and any other contact details. "
            "Source should be 'twitter'."
        ),
        agent=agent,
    )


def make_email_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Discover email addresses and phone numbers for key people at '{company}'. "
            "First, run a Hunter.io domain search to find the email pattern and all known contacts. "
            "Then search Apollo.io for the top executives (CEO, CTO, CFO, VP-level, directors). "
            "For each person already found by other agents, use the Hunter email finder to "
            "verify or discover their email. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array. Each person must include: "
            "name, title, email (list), phone (list), and confidence score. "
            "Include the Hunter.io confidence score as the confidence field. "
            "Source should be 'hunter' or 'apollo'."
        ),
        agent=agent,
    )


def make_github_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Find technical team members at '{company}' via GitHub. "
            "Search for the company's GitHub organization(s), list public members, "
            "and enrich each profile for email, website, bio, and location. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array. Each person must include: "
            "name, github_username, email (from public profile), website, bio. "
            "Source should be 'github'."
        ),
        agent=agent,
    )


def make_news_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Search news and press releases to find executives and key people at '{company}'. "
            "Look for CEO announcements, new hires, board appointments, and interviews. "
            "Extract full names, titles, and any contact details mentioned. "
            "Also search for the company's 'About' or 'Leadership' page. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array. Each person must include: "
            "name, title, and any contact details found. "
            "Source should be 'news' or 'web'."
        ),
        agent=agent,
    )


def make_web_search_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Perform broad OSINT web searches to find all key people at '{company}'. "
            "Search for:\n"
            f"  1. '{company} leadership team site:company-website'\n"
            f"  2. '{company} CEO founder executive interview'\n"
            f"  3. '{company}' site:crunchbase.com OR site:angel.co\n"
            f"  4. '{company}' site:producthunt.com\n"
            f"  5. '{company}' keynote OR speaker conference\n"
            "Collect names, titles, emails, social handles, and personal websites. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array covering executives, founders, and notable "
            "employees found across any public web source. Source should be 'web'."
        ),
        agent=agent,
    )


def make_enrichment_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Enrich the company '{company}' via Clearbit to find its domain, industry, "
            "size, LinkedIn/Twitter handles, and executive contacts. "
            "Use the company domain to search for additional contacts via Clearbit Prospector. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array of Clearbit-sourced executives. "
            "Source should be 'clearbit'."
        ),
        agent=agent,
    )


def make_merger_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"You will receive the aggregated output from all research agents for '{company}'. "
            "Your job:\n"
            "1. Parse every JSON block in the context.\n"
            "2. Identify duplicate records (same person at same company — match by full name "
            "   using fuzzy matching, allowing for minor spelling differences).\n"
            "3. Merge duplicates: combine all contact channels (emails, phones, social handles) "
            "   into one record; keep the most complete title; union the sources list.\n"
            "4. Remove entirely empty records.\n"
            "5. Sort the final list by confidence score descending.\n"
            "6. Output ONLY a single valid JSON object with a 'people' key.\n\n"
            "The JSON schema for each person:\n"
            f"{PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A single valid JSON object: {\"people\": [...]} "
            "containing all deduplicated, merged contact records. "
            "No extra prose — just the JSON."
        ),
        agent=agent,
        context=[],  # Will be populated dynamically in the crew
    )
