"""
Post-process crew output: parse JSON blocks, deduplicate, merge contact records.
This runs deterministically after the LLM merger agent to catch any remaining duplicates.
"""

import json
import re
from .models.person import PersonContact, CompanySearchResult

try:
    from rapidfuzz import fuzz
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _names_match(a: str, b: str, threshold: int = 88) -> bool:
    na, nb = _normalize_name(a), _normalize_name(b)
    if na == nb:
        return True
    if _HAS_RAPIDFUZZ:
        # token_set_ratio handles middle initials and word reordering gracefully
        return fuzz.token_set_ratio(na, nb) >= threshold
    # Simple fallback: check if one name is contained in the other
    parts_a = set(na.split())
    parts_b = set(nb.split())
    overlap = len(parts_a & parts_b)
    return overlap >= min(2, min(len(parts_a), len(parts_b)))


def _extract_json_blocks(text: str) -> list[dict]:
    """Extract all JSON objects from a potentially mixed text string."""
    blocks: list[dict] = []

    # Try full parse first
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict):
            blocks.append(obj)
            return blocks
    except Exception:
        pass

    # Extract fenced JSON blocks
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE):
        try:
            obj = json.loads(match.group(1).strip())
            if isinstance(obj, dict):
                blocks.append(obj)
        except Exception:
            pass

    # Extract bare {...} objects
    for match in re.finditer(r"\{[\s\S]*?\}", text):
        try:
            obj = json.loads(match.group())
            if isinstance(obj, dict) and "people" in obj:
                blocks.append(obj)
        except Exception:
            pass

    return blocks


def parse_agent_output(raw: str, source_tag: str = "unknown") -> list[PersonContact]:
    """Parse raw agent output into PersonContact records."""
    people: list[PersonContact] = []
    blocks = _extract_json_blocks(raw)

    for block in blocks:
        for p in block.get("people", []):
            if not p.get("name"):
                continue
            if source_tag not in p.get("sources", []):
                p.setdefault("sources", []).append(source_tag)
            try:
                people.append(PersonContact(**p))
            except Exception:
                # Best-effort: extract minimum fields
                people.append(PersonContact(
                    name=str(p.get("name", "")),
                    title=p.get("title"),
                    email=p.get("email", []) if isinstance(p.get("email"), list) else [p.get("email", "")],
                    sources=[source_tag],
                ))
    return people


def merge_results(all_people: list[PersonContact], company: str) -> CompanySearchResult:
    """Deduplicate and merge all PersonContact records."""
    merged: list[PersonContact] = []

    for person in all_people:
        if not person.name:
            continue

        matched = False
        for i, existing in enumerate(merged):
            if _names_match(existing.name, person.name):
                merged[i] = existing.merge(person)
                matched = True
                break

        if not matched:
            merged.append(person.model_copy(deep=True))

    # Sort by confidence desc, then by number of contact channels desc
    merged.sort(
        key=lambda p: (p.confidence, len(p.email) + len(p.phone) + bool(p.linkedin_url)),
        reverse=True,
    )

    return CompanySearchResult(
        company=company,
        people=merged,
        search_metadata={"total_unique_people": len(merged)},
    )
