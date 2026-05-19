import httpx
import logging
from config import get_settings

logger = logging.getLogger(__name__)

HUNTER_TIMEOUT = httpx.Timeout(60.0, connect=30.0)

settings = get_settings()

# In-memory cache for Hunter email results
_hunter_cache: dict[str, dict] = {}

# Map roles to Hunter seniority/department filters
SENIORITY_MAP = {
    "ceo": "senior", "cto": "senior", "cfo": "senior", "coo": "senior",
    "vp": "senior", "vice president": "senior", "director": "senior",
    "founder": "senior", "co-founder": "senior", "president": "senior",
    "head": "senior", "chief": "senior", "partner": "senior",
    "manager": "management", "lead": "management", "supervisor": "management",
    "intern": "junior", "assistant": "junior", "associate": "junior",
}

DEPARTMENT_MAP = {
    "engineer": "it", "developer": "it", "devops": "it", "software": "it",
    "cto": "it", "tech": "it", "data": "it", "architect": "it",
    "marketing": "marketing", "growth": "marketing", "content": "marketing",
    "seo": "marketing", "brand": "marketing", "cmo": "marketing",
    "sales": "sales", "account": "sales", "business development": "sales",
    "hr": "human_resources", "people": "human_resources", "talent": "human_resources",
    "finance": "finance", "cfo": "finance", "accounting": "finance",
    "ceo": "executive", "founder": "executive", "president": "executive",
    "coo": "executive", "co-founder": "executive",
}


def _roles_to_filters(roles: list[str]) -> tuple[list[str], list[str]]:
    """Convert role titles to Hunter seniority and department filters."""
    seniorities = set()
    departments = set()
    for role in roles:
        role_lower = role.lower()
        for key, val in SENIORITY_MAP.items():
            if key in role_lower:
                seniorities.add(val)
        for key, val in DEPARTMENT_MAP.items():
            if key in role_lower:
                departments.add(val)
    return list(seniorities), list(departments)


async def find_leads_hunter(
    domains: list[str], roles: list[str], limit: int = 50
) -> list[dict]:
    """Search Hunter.io for leads at target company domains."""
    if not settings.hunter_api_key:
        return _generate_mock_leads(domains, roles, limit)

    seniorities, departments = _roles_to_filters(roles)
    leads = []
    per_domain = max(10, limit // max(len(domains), 1))

    async with httpx.AsyncClient(timeout=HUNTER_TIMEOUT) as client:
        for domain in domains:
            domain = domain.strip().lower()
            if not domain:
                continue

            params = {
                "domain": domain,
                "api_key": settings.hunter_api_key,
                "limit": min(per_domain, 100),
            }
            if seniorities:
                params["seniority"] = ",".join(seniorities)
            if departments:
                params["department"] = ",".join(departments)

            response = await client.get(
                "https://api.hunter.io/v2/domain-search", params=params
            )
            if response.status_code != 200:
                continue

            data = response.json().get("data", {})
            company_name = data.get("organization", domain)
            emails = data.get("emails", [])

            for e in emails:
                email_addr = e.get("value", "")
                if not email_addr:
                    continue
                leads.append({
                    "first_name": e.get("first_name", ""),
                    "last_name": e.get("last_name", ""),
                    "email": email_addr,
                    "company": company_name,
                    "title": e.get("position", ""),
                    "linkedin_url": e.get("linkedin", "") or "",
                    "domain": domain,
                    "confidence": e.get("confidence", 0),
                    "department": e.get("department", ""),
                    "seniority": e.get("seniority", ""),
                })

            if len(leads) >= limit:
                break

    return leads[:limit]


async def find_email_hunter(domain: str, first_name: str, last_name: str) -> dict:
    """Find a specific person's email using Hunter.io Email Finder."""
    cache_key = f"{domain}:{first_name}:{last_name}"
    if cache_key in _hunter_cache:
        return _hunter_cache[cache_key]

    if not settings.hunter_api_key:
        result = {"email": f"{first_name.lower()}.{last_name.lower()}@{domain}", "confidence": 85, "source": "mock"}
        _hunter_cache[cache_key] = result
        return result

    async with httpx.AsyncClient(timeout=HUNTER_TIMEOUT) as client:
        response = await client.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": settings.hunter_api_key,
            },
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            email = data.get("email", "")
            result = {
                "email": email,
                "confidence": data.get("score", 0),
                "source": "hunter",
            }
            _hunter_cache[cache_key] = result
            return result

    return {"email": "", "confidence": 0, "source": "not_found"}


async def verify_email_hunter(email: str) -> str:
    """Verify an email address using Hunter.io. Returns: valid, risky, or invalid."""
    if not settings.hunter_api_key:
        if "@" in email and "." in email.split("@")[-1]:
            return "valid"
        return "invalid"

    retries = 3
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=HUNTER_TIMEOUT) as client:
                response = await client.get(
                    "https://api.hunter.io/v2/email-verifier",
                    params={"email": email, "api_key": settings.hunter_api_key},
                )
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    status = data.get("status", "")
                    result = data.get("result", "")
                    if result == "deliverable" or status == "valid":
                        return "valid"
                    elif result == "risky" or status == "accept_all":
                        return "risky"
                    elif result == "undeliverable" or status == "invalid":
                        return "invalid"
                    return "risky"
                return "risky"
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            logger.warning(f"Hunter verify attempt {attempt+1}/{retries} failed for {email}: {e}")
            if attempt == retries - 1:
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
                "email": f"{first.lower()}.{last.lower()}@{domain}",
                "company": company,
                "title": role if role else default_title,
                "linkedin_url": f"https://linkedin.com/in/{first.lower()}{last.lower()}",
                "domain": domain,
            })
        if len(leads) >= limit:
            break
    return leads[:limit]
