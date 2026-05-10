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

# Seniority tiers used in both task prompts and deterministic ranking
SENIORITY_TITLES = (
    "CEO, Co-CEO, President, Founder, Co-Founder, Executive Chairman, "
    "CTO, CFO, COO, CMO, CPO, CISO, CRO, CLO, CXO, "
    "SVP, EVP, Senior Vice President, Executive Vice President, "
    "VP, Vice President, General Manager, Managing Director, "
    "Director, Head of, Principal, "
    "Senior Manager, Manager, Lead, Senior, Staff"
)


def make_linkedin_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Find the most senior executives and decision-makers at '{company}' via LinkedIn. "
            "PRIORITY TARGETS (search in this order):\n"
            f"  1. C-suite: CEO, CTO, CFO, COO, CMO, CPO, CISO, President, Executive Chairman\n"
            f"  2. Founders and co-founders\n"
            f"  3. SVP / EVP level\n"
            f"  4. VP level\n"
            f"  5. Directors and Heads of departments\n"
            "Use Hunter.io domain search to find email addresses for each person found. "
            "Search site:linkedin.com for each title explicitly: "
            f"'site:linkedin.com \"{company}\" CEO', 'site:linkedin.com \"{company}\" CTO', etc. "
            "Collect full names, exact job titles, LinkedIn URLs, emails, and phone numbers. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array focused on the most senior people. "
            "Each person must include name, title, and any available email/phone/linkedin_url. "
            "Source should be 'linkedin'."
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
            f"Discover verified email addresses and phone numbers for senior executives at '{company}'. "
            "Steps:\n"
            "1. Run a Hunter.io domain search to get the email pattern and all known contacts.\n"
            "2. Search Apollo.io specifically for C-suite, VPs, Directors, and founders — "
            "   use title filters: CEO, CTO, CFO, COO, CMO, CPO, SVP, EVP, VP, Director, Head, Founder.\n"
            "3. For each named executive found by any agent, run the Hunter email finder "
            "   to verify or discover their specific email address.\n"
            "4. Prioritise people with the most senior titles.\n"
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array focused on senior contacts. "
            "Each person must include name, title, email (list), phone (list), confidence score. "
            "Source should be 'hunter' or 'apollo'."
        ),
        agent=agent,
    )


def make_github_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Find technical leadership at '{company}' via GitHub. "
            "Search for the company's GitHub organization(s), identify owners and admins first, "
            "then list public members. Look especially for CTO, VP Engineering, "
            "Principal/Staff Engineers, and Engineering Directors. "
            "Enrich each profile for email, website, bio, and location. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array prioritising technical leadership. "
            "Each person must include name, github_username, email (from public profile), "
            "website, bio. Source should be 'github'."
        ),
        agent=agent,
    )


def make_news_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Find senior executives and board members at '{company}' via news and press coverage. "
            "Search for:\n"
            f"  1. '{company} CEO OR CTO OR CFO OR founder interview'\n"
            f"  2. '{company} executive appointment OR named OR joins OR promoted'\n"
            f"  3. '{company} board of directors OR advisory board'\n"
            f"  4. '{company} leadership team' site:company-domain\n"
            f"  5. '{company}' site:crunchbase.com for founder/exec data\n"
            f"  6. '{company}' site:bloomberg.com OR site:forbes.com OR site:techcrunch.com\n"
            "Extract full names, exact titles, and any contact details mentioned. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array of executives and board members. "
            "Each person must include name, title, and any contact details found. "
            "Source should be 'news' or 'web'."
        ),
        agent=agent,
    )


def make_web_search_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Perform targeted OSINT web searches to find the most senior people at '{company}'. "
            "Execute ALL of the following searches:\n"
            f"  1. '{company} leadership team' OR '{company} executive team'\n"
            f"  2. '{company} CEO' OR '{company} founder' OR '{company} president'\n"
            f"  3. '{company} CTO' OR '{company} CFO' OR '{company} COO'\n"
            f"  4. '{company} VP' OR '{company} vice president' OR '{company} SVP'\n"
            f"  5. '{company} board of directors' OR '{company} advisory board'\n"
            f"  6. site:crunchbase.com '{company}'\n"
            f"  7. site:angel.co OR site:wellfound.com '{company}'\n"
            f"  8. site:linkedin.com/in '{company}' CEO OR CTO OR CFO OR founder\n"
            f"  9. '{company}' keynote speaker OR conference OR TED OR podcast interview\n"
            f" 10. '{company} about page' OR '{company} team page'\n"
            "Collect names, exact titles, emails, social handles, and personal websites. "
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array covering executives and founders "
            "found across any public web source. Source should be 'web'."
        ),
        agent=agent,
    )


def make_enrichment_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Enrich the company '{company}' via Hunter.io and extract its most senior contacts. "
            "Steps:\n"
            "1. Use Hunter company enrichment to get the domain, industry, size, LinkedIn, Twitter.\n"
            "2. Run Hunter domain search and filter for senior titles only: "
            f"   {SENIORITY_TITLES}.\n"
            "3. For each executive found, attempt Hunter email finder to get verified email.\n"
            f"Return results as JSON matching this schema: {PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A JSON object with a 'people' array of Hunter-sourced senior executives. "
            "Source should be 'hunter'."
        ),
        agent=agent,
    )


def make_merger_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"Aggregate all research agent outputs for '{company}' into one clean list.\n"
            "Steps:\n"
            "1. Parse every JSON block in the context.\n"
            "2. Identify duplicates (same person — fuzzy name match) and merge their records: "
            "   combine emails, phones, social handles; keep the most complete title; union sources.\n"
            "3. Remove empty records.\n"
            "4. Output ONLY a single valid JSON object with a 'people' key.\n\n"
            f"Schema:\n{PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A single valid JSON object: {\"people\": [...]} "
            "with all deduplicated, merged contact records. No extra prose — just the JSON."
        ),
        agent=agent,
        context=[],  # populated dynamically in the crew
    )


def make_ranker_task(agent: Agent, company: str) -> Task:
    return Task(
        description=(
            f"You will receive a merged list of people found at '{company}'. "
            "Your job is to sort them from most senior to most junior based on their title, "
            "and add a 'seniority_rank' integer to each record (1 = most senior).\n\n"
            "Seniority tier order (highest to lowest):\n"
            "  Tier 1 — Founder, Co-Founder, CEO, Co-CEO, President, Executive Chairman, Board Member\n"
            "  Tier 2 — CTO, CFO, COO, CMO, CPO, CISO, CRO, CLO, and other C-suite\n"
            "  Tier 3 — EVP, SVP (Executive/Senior Vice President)\n"
            "  Tier 4 — VP, Vice President, General Manager, Managing Director\n"
            "  Tier 5 — Director, Head of [department], Principal\n"
            "  Tier 6 — Senior Manager, Manager, Lead\n"
            "  Tier 7 — Senior [IC title], Staff [IC title]\n"
            "  Tier 8 — All other / unknown titles\n\n"
            "Rules:\n"
            "- Do NOT remove any records or alter contact data.\n"
            "- Do NOT merge records — that was already done.\n"
            "- Add 'seniority_rank' integer field to every record.\n"
            "- Within the same tier, order alphabetically by name.\n"
            "- Output ONLY a single valid JSON object with a 'people' key.\n\n"
            f"Schema (same as input, plus seniority_rank):\n{PERSON_JSON_SCHEMA}"
        ),
        expected_output=(
            "A single valid JSON object: {\"people\": [...]} "
            "sorted from most senior to most junior, each record having a 'seniority_rank' field. "
            "No extra prose — just the JSON."
        ),
        agent=agent,
        context=[],  # populated dynamically in the crew
    )
