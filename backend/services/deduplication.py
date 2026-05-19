from datetime import datetime, timedelta
from database import get_db


async def check_suppression(email: str) -> tuple[bool, str]:
    """Check if email is on the suppression list."""
    db = get_db()
    entry = await db.suppression_list.find_one({"email": email})
    if entry:
        return True, entry.get("reason", "")
    return False, ""


async def check_cooldown(lead: dict, days: int = 30) -> tuple[bool, str]:
    """Check if lead was contacted within the cooldown period."""
    last_contacted = lead.get("last_contacted_at")
    if last_contacted:
        cooldown_end = last_contacted + timedelta(days=days)
        if datetime.utcnow() < cooldown_end:
            return True, f"Contacted {last_contacted.strftime('%Y-%m-%d')}, cooldown until {cooldown_end.strftime('%Y-%m-%d')}"
    return False, ""


async def check_already_pitched(lead: dict, product_url: str) -> tuple[bool, str]:
    """Check if this product was already pitched to this lead."""
    pitched = lead.get("pitched_products", []) or []
    if product_url in pitched:
        return True, f"Already pitched {product_url}"
    return False, ""


async def run_deduplication(lead: dict, product_url: str) -> tuple[bool, str]:
    """Run all deduplication checks. Returns (should_drop, reason)."""
    # Check 1: Suppression list
    is_suppressed, reason = await check_suppression(lead.get("email", ""))
    if is_suppressed:
        return True, f"Suppressed: {reason}"

    # Check 2: 30-day cooldown
    in_cooldown, reason = await check_cooldown(lead)
    if in_cooldown:
        return True, f"Cooldown: {reason}"

    # Check 3: Already pitched this product
    already_pitched, reason = await check_already_pitched(lead, product_url)
    if already_pitched:
        return True, f"Already pitched: {reason}"

    return False, ""

    return False, ""
