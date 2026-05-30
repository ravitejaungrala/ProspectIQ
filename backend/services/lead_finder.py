import httpx
import logging
from config import get_settings

logger = logging.getLogger(__name__)

APOLLO_TIMEOUT = httpx.Timeout(60.0, connect=30.0)
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"

settings = get_settings()

# In-memory cache for Apollo email results
_apollo_cache: dict[str, dict] = {}

# Placeholder values that should be treated as "no key configured".
_APOLLO_KEY_PLACEHOLDERS = {
    "", "your-apollo-api-key-here", "your-apollo-key-here", "changeme",
}


def _apollo_key() -> str:
    """Return the Apollo API key, treating placeholder values as unset."""
    key = (settings.apollo_api_key or "").strip()
    return "" if key in _APOLLO_KEY_PLACEHOLDERS else key


# Map role keywords to Apollo `person_seniorities` filter values.
# Apollo accepts: owner, founder, c_suite, partner, vp, head, director,
# manager, senior, entry, intern.
SENIORITY_MAP = {
    "ceo": "c_suite", "cto": "c_suite", "cfo": "c_suite", "coo": "c_suite",
    "chief": "c_suite", "president": "c_suite",
    "vp": "vp", "vice president": "vp",
    "director": "director",
    "founder": "founder", "co-founder": "founder", "owner": "owner",
    "head": "head", "partner": "partner",
    "manager": "manager", "lead": "manager", "supervisor": "manager",
    "senior": "senior", "associate": "entry", "assistant": "entry",
    "intern": "intern",
}


def _apollo_headers() -> dict:
    """Standard headers for Apollo API requests."""
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": _apollo_key(),
    }


def _roles_to_seniorities(roles: list[str]) -> list[str]:
    """Convert role titles to Apollo `person_seniorities` filter values."""
    seniorities = set()
    for role in roles:
        role_lower = role.lower()
        for key, val in SENIORITY_MAP.items():
            if key in role_lower:
                seniorities.add(val)
    return list(seniorities)


def _email_status_to_confidence(email_status: str) -> int:
    """Map an Apollo email_status string to a 0-100 confidence score."""
    return {
        "verified": 95,
        "likely to engage": 75,
        "likely_to_engage": 75,
        "extrapolated": 55,
        "guessed": 50,
        "unverified": 40,
        "unavailable": 0,
        "bounced": 0,
    }.get((email_status or "").lower(), 50)


def _is_unlocked_email(email: str) -> bool:
    """True when Apollo returned a real email (not a locked placeholder)."""
    if not email:
        return False
    if "email_not_unlocked" in email.lower():
        return False
    if email.lower().startswith("not_unlocked"):
        return False
    return "@" in email


async def find_leads_apollo(
    domains: list[str], roles: list[str], limit: int = 50
) -> list[dict]:
    """Search Apollo.io for leads at target company domains.

    Runs a People Search, then enriches every match via People Match so
    real (unlocked) email addresses and email_status values are returned.
    """
    if not _apollo_key():
        return _generate_mock_leads(domains, roles, limit)

    clean_domains = [d.strip().lower() for d in domains if d and d.strip()]
    if not clean_domains:
        return []

    seniorities = _roles_to_seniorities(roles)
    leads: list[dict] = []

    async with httpx.AsyncClient(timeout=APOLLO_TIMEOUT) as client:
        # --- Stage 1: People Search ---
        page = 1
        per_page = min(max(limit, 1), 100)
        while len(leads) < limit:
            payload: dict = {
                "q_organization_domains_list": clean_domains,
                "page": page,
                "per_page": per_page,
            }
            if roles:
                payload["person_titles"] = roles
            if seniorities:
                payload["person_seniorities"] = seniorities

            try:
                response = await client.post(
                    f"{APOLLO_BASE_URL}/mixed_people/search",
                    headers=_apollo_headers(),
                    json=payload,
                )
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as exc:
                logger.warning(f"Apollo people search failed: {exc}")
                break

            if response.status_code != 200:
                logger.warning(
                    f"Apollo people search returned {response.status_code}: {response.text[:200]}"
                )
                break

            body = response.json()
            people = body.get("people", []) or []
            if not people:
                break

            for person in people:
                if len(leads) >= limit:
                    break
                lead = _person_to_lead(person)
                if lead:
                    leads.append(lead)

            pagination = body.get("pagination", {}) or {}
            total_pages = pagination.get("total_pages", page)
            if page >= total_pages:
                break
            page += 1

        # --- Stage 2: Enrich each lead to reveal real emails ---
        for lead in leads:
            if _is_unlocked_email(lead.get("email", "")):
                continue
            enriched = await _match_person(
                client,
                apollo_id=lead.get("apollo_id"),
                domain=lead.get("domain", ""),
                first_name=lead.get("first_name", ""),
                last_name=lead.get("last_name", ""),
            )
            if enriched:
                if _is_unlocked_email(enriched.get("email", "")):
                    lead["email"] = enriched["email"]
                lead["email_status"] = enriched.get("email_status", lead.get("email_status", ""))
                lead["confidence"] = _email_status_to_confidence(lead["email_status"])

    # Drop leads that still have no usable email after enrichment.
    return [l for l in leads if _is_unlocked_email(l.get("email", ""))][:limit]


def _person_to_lead(person: dict) -> dict | None:
    """Convert an Apollo person object into the internal lead shape."""
    org = person.get("organization") or {}
    domain = (org.get("primary_domain") or "").lower()
    if not domain:
        website = org.get("website_url") or ""
        domain = website.replace("https://", "").replace("http://", "").split("/")[0].lower()

    email = person.get("email", "") or ""
    email_status = person.get("email_status", "") or ""

    return {
        "apollo_id": person.get("id", ""),
        "first_name": person.get("first_name", "") or "",
        "last_name": person.get("last_name", "") or "",
        "email": email,
        "company": org.get("name", "") or domain,
        "title": person.get("title", "") or "",
        "linkedin_url": person.get("linkedin_url", "") or "",
        "domain": domain,
        "confidence": _email_status_to_confidence(email_status),
        "email_status": email_status,
        "seniority": person.get("seniority", "") or "",
        "department": (person.get("departments") or [""])[0] if person.get("departments") else "",
    }


async def _match_person(
    client: httpx.AsyncClient,
    apollo_id: str = "",
    domain: str = "",
    first_name: str = "",
    last_name: str = "",
    email: str = "",
) -> dict | None:
    """Call Apollo People Match to reveal/verify a single person's email."""
    payload: dict = {"reveal_personal_emails": True}
    if apollo_id:
        payload["id"] = apollo_id
    if email:
        payload["email"] = email
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    if domain:
        payload["domain"] = domain

    try:
        response = await client.post(
            f"{APOLLO_BASE_URL}/people/match",
            headers=_apollo_headers(),
            json=payload,
        )
    except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as exc:
        logger.warning(f"Apollo people match failed: {exc}")
        return None

    if response.status_code != 200:
        logger.warning(
            f"Apollo people match returned {response.status_code}: {response.text[:200]}"
        )
        return None

    person = response.json().get("person") or {}
    if not person:
        return None
    return {
        "email": person.get("email", "") or "",
        "email_status": person.get("email_status", "") or "",
    }


async def find_email_apollo(domain: str, first_name: str, last_name: str) -> dict:
    """Find a specific person's email using Apollo People Match."""
    cache_key = f"{domain}:{first_name}:{last_name}"
    if cache_key in _apollo_cache:
        return _apollo_cache[cache_key]

    if not _apollo_key():
        mock_email = first_name.lower() + "." + last_name.lower() + "@" + domain
        result = {"email": mock_email, "confidence": 85, "source": "mock"}
        _apollo_cache[cache_key] = result
        return result

    async with httpx.AsyncClient(timeout=APOLLO_TIMEOUT) as client:
        matched = await _match_person(
            client, domain=domain, first_name=first_name, last_name=last_name
        )

    if matched and _is_unlocked_email(matched.get("email", "")):
        result = {
            "email": matched["email"],
            "confidence": _email_status_to_confidence(matched.get("email_status", "")),
            "source": "apollo",
        }
        _apollo_cache[cache_key] = result
        return result

    return {"email": "", "confidence": 0, "source": "not_found"}


async def verify_email_apollo(email: str) -> str:
    """Verify an email address using Apollo. Returns: valid, risky, or invalid."""
    if not _apollo_key():
        if "@" in email and "." in email.split("@")[-1]:
            return "valid"
        return "invalid"

    retries = 3
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=APOLLO_TIMEOUT) as client:
                matched = await _match_person(client, email=email)
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as exc:
            logger.warning(
                f"Apollo verify attempt {attempt+1}/{retries} failed for {email}: {exc}"
            )
            if attempt == retries - 1:
                return "risky"
            continue

        if matched is None:
            # No match found / API error -> treat conservatively.
            return "risky"

        status = (matched.get("email_status", "") or "").lower()
        if status == "verified":
            return "valid"
        if status in ("unavailable", "bounced", "invalid"):
            return "invalid"
        # unverified, guessed, extrapolated, likely to engage, empty, etc.
        return "risky"

    return "risky"


def _generate_mock_leads(domains: list[str], roles: list[str], limit: int) -> list[dict]:
    """Generate mock leads for demo/testing when no API key."""
    mock_people = [
        ("James", "Wilson", "CEO"), ("Sarah", "Chen", "CTO"),
        ("Michael", "Kumar", "VP Engineering"), ("Emily", "Thompson", "Head of Marketing"),
        ("David", "Garcia", "Director of Sales"), ("Lisa", "Anderson", "CFO"),
        ("Robert", "Lee", "Product Manager"), ("Jennifer", "Martinez", "VP Sales"),
        ("William", "Brown", "Director of Engineering"), ("Jessica", "Taylor", "CMO"),
    ]
    role = roles[0] if roles else "VP of Engineering"
    leads = []
    for domain in (domains or ["example.com"]):
        domain = domain.strip().lower()
        company = domain.split(".")[0].title()
        for i, (first, last, default_title) in enumerate(mock_people):
            if len(leads) >= limit:
                break
            leads.append({
                "first_name": first,
                "last_name": last,
                "email": first.lower() + "." + last.lower() + "@" + domain,
                "company": company,
                "title": role if role else default_title,
                "linkedin_url": "https://linkedin.com/in/" + first.lower() + last.lower(),
                "domain": domain,
            })
        if len(leads) >= limit:
            break
    return leads[:limit]
