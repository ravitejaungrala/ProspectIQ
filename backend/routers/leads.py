import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from database import get_db

logger = logging.getLogger(__name__)
from models import new_lead, doc_to_dict
from schemas import LeadOut, LeadSearchParams
from services.lead_finder import find_leads_hunter, verify_email_hunter
from services.ai_service import score_lead_fit
from services.deduplication import run_deduplication

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/campaign/{campaign_id}", response_model=list[LeadOut])
async def get_campaign_leads(campaign_id: str, status: str = None):
    db = get_db()
    query = {"campaign_id": campaign_id}
    if status:
        query["status"] = status
    cursor = db.leads.find(query).sort("profile_score", -1)
    leads = await cursor.to_list(500)
    return [doc_to_dict(l) for l in leads]


@router.post("/campaign/{campaign_id}/find", response_model=list[LeadOut])
async def find_leads(campaign_id: str, params: LeadSearchParams):
    """Stage 2: Find leads using Hunter.io."""
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    domains = params.domains or []
    roles = params.roles or campaign.get("roles", [])

    if not domains:
        raise HTTPException(status_code=400, detail="Please provide at least one target company domain (e.g. google.com)")

    raw_leads = await find_leads_hunter(domains, roles, params.limit)

    created_leads = []
    for raw in raw_leads:
        # Check if lead already exists in this campaign
        existing = await db.leads.find_one({"campaign_id": campaign_id, "email": raw["email"]})
        if existing:
            continue

        lead = new_lead(
            campaign_id=campaign_id,
            first_name=raw["first_name"],
            last_name=raw["last_name"],
            email=raw["email"],
            company=raw["company"],
            title=raw["title"],
            linkedin_url=raw.get("linkedin_url", ""),
            domain=raw.get("domain", ""),
            status="raw",
        )
        await db.leads.insert_one(lead)
        created_leads.append(doc_to_dict(lead))

    await db.campaigns.update_one(
        {"_id": campaign_id},
        {"$set": {"status": "verifying", "updated_at": datetime.utcnow()}},
    )

    return created_leads


@router.post("/campaign/{campaign_id}/verify")
async def verify_and_score_leads(campaign_id: str, background_tasks: BackgroundTasks):
    """Stage 3: Verify, score, and deduplicate leads."""
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    background_tasks.add_task(_verify_score_deduplicate, campaign_id)
    return {"message": "Verification started", "campaign_id": campaign_id}


async def _verify_score_deduplicate(campaign_id: str):
    """Background: Run the full Stage 3 pipeline."""
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        return

    leads = await db.leads.find({"campaign_id": campaign_id, "status": "raw"}).to_list(500)

    for lead in leads:
        lead_id = lead["_id"]

        # Step 1: Verify email
        try:
            email_status = await verify_email_hunter(lead["email"])
        except Exception as exc:
            logger.warning(f"Email verification failed for {lead['email']}: {exc}")
            email_status = "risky"

        if email_status == "invalid":
            await db.leads.update_one(
                {"_id": lead_id},
                {"$set": {"email_status": email_status, "status": "dropped", "drop_reason": "Invalid email", "updated_at": datetime.utcnow()}},
            )
            continue

        await db.leads.update_one(
            {"_id": lead_id},
            {"$set": {"email_status": email_status, "status": "verified", "updated_at": datetime.utcnow()}},
        )

        # Step 2: Score lead fit
        try:
            score = await score_lead_fit(
                {"first_name": lead["first_name"], "last_name": lead["last_name"],
                 "title": lead["title"], "company": lead["company"],
                 "industries": campaign.get("industries", []), "roles": campaign.get("roles", [])},
                campaign.get("ideal_customer_profile", {}),
            )
        except Exception:
            score = 50.0

        if score < 30:
            await db.leads.update_one(
                {"_id": lead_id},
                {"$set": {"profile_score": score, "status": "dropped", "drop_reason": f"Low score: {score}", "updated_at": datetime.utcnow()}},
            )
            continue

        await db.leads.update_one(
            {"_id": lead_id},
            {"$set": {"profile_score": score, "status": "scored", "updated_at": datetime.utcnow()}},
        )

        # Step 3: Deduplication
        lead_fresh = await db.leads.find_one({"_id": lead_id})
        should_drop, reason = await run_deduplication(lead_fresh, campaign["product_url"])
        if should_drop:
            await db.leads.update_one(
                {"_id": lead_id},
                {"$set": {"status": "dropped", "drop_reason": reason, "updated_at": datetime.utcnow()}},
            )
            continue

        await db.leads.update_one(
            {"_id": lead_id},
            {"$set": {"status": "clean", "updated_at": datetime.utcnow()}},
        )

    await db.campaigns.update_one(
        {"_id": campaign_id},
        {"$set": {"status": "outreach", "updated_at": datetime.utcnow()}},
    )


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: str):
    db = get_db()
    lead = await db.leads.find_one({"_id": lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return doc_to_dict(lead)


@router.patch("/{lead_id}/status")
async def update_lead_status(lead_id: str, status: str):
    db = get_db()
    result = await db.leads.update_one(
        {"_id": lead_id},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Status updated"}
