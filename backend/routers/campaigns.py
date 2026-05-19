from fastapi import APIRouter, HTTPException, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from database import get_db
from models import new_campaign, doc_to_dict
from schemas import CampaignCreate, CampaignOut, CampaignListOut, CampaignUpdate
from services.scraper import scrape_website
from services.ai_service import extract_product_info

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignOut)
async def create_campaign(data: CampaignCreate, background_tasks: BackgroundTasks):
    """Stage 1: Create campaign from product URL. Scrapes website and extracts ICP."""
    db = get_db()
    campaign = new_campaign(data.product_url)
    # Store sender info from request
    campaign["sender_name"] = data.sender_name
    campaign["sender_title"] = data.sender_title
    campaign["sender_email"] = data.sender_email
    campaign["sender_phone"] = data.sender_phone
    await db.campaigns.insert_one(campaign)

    background_tasks.add_task(_process_campaign, campaign["_id"], data.product_url)

    out = doc_to_dict(campaign)
    out["lead_count"] = 0
    return out


async def _process_campaign(campaign_id: str, product_url: str):
    """Background task: scrape website and extract product info with AI."""
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        return

    try:
        scrape_result = await scrape_website(product_url)
        content = scrape_result["content"]
        info = await extract_product_info(content)

        # Merge demo video: prefer scraper's HTML extraction, fallback to AI
        demo_video = scrape_result.get("demo_video_url", "") or info.get("demo_video_url", "")
        phone = scrape_result.get("phone", "") or info.get("phone", "")
        calendly_url = scrape_result.get("calendly_url", "")
        demo_booking_url = scrape_result.get("demo_booking_url", "") or calendly_url

        await db.campaigns.update_one(
            {"_id": campaign_id},
            {"$set": {
                "product_name": info.get("product_name", ""),
                "product_summary": info.get("product_summary", ""),
                "ideal_customer_profile": info.get("ideal_customer_profile", {}),
                "industries": info.get("industries", []),
                "roles": info.get("roles", []),
                "pain_points": info.get("pain_points", []),
                "demo_video_url": demo_video,
                "calendly_url": calendly_url,
                "demo_booking_url": demo_booking_url,
                "product_phone": phone,
                "contact_emails": scrape_result.get("emails", []),
                "social_links": scrape_result.get("social_links", {}),
                "target_domains": info.get("target_domains", []),
                "status": "finding_leads",
                "updated_at": datetime.utcnow(),
            }},
        )
    except Exception as e:
        await db.campaigns.update_one(
            {"_id": campaign_id},
            {"$set": {
                "product_name": f"Error: {str(e)[:100]}",
                "status": "setup",
                "updated_at": datetime.utcnow(),
            }},
        )


@router.get("", response_model=list[CampaignListOut])
async def list_campaigns():
    db = get_db()
    campaigns = await db.campaigns.find().sort("created_at", -1).to_list(100)

    out = []
    for c in campaigns:
        lead_count = await db.leads.count_documents({"campaign_id": c["_id"]})
        d = doc_to_dict(c)
        d["lead_count"] = lead_count
        out.append(d)
    return out


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(campaign_id: str):
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    lead_count = await db.leads.count_documents({"campaign_id": campaign_id})
    out = doc_to_dict(campaign)
    out["lead_count"] = lead_count
    return out


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(campaign_id: str, data: CampaignUpdate):
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    updates = {"updated_at": datetime.utcnow()}
    if data.product_name is not None:
        updates["product_name"] = data.product_name
    if data.status is not None:
        updates["status"] = data.status

    await db.campaigns.update_one({"_id": campaign_id}, {"$set": updates})

    campaign = await db.campaigns.find_one({"_id": campaign_id})
    lead_count = await db.leads.count_documents({"campaign_id": campaign_id})
    out = doc_to_dict(campaign)
    out["lead_count"] = lead_count
    return out


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str):
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Cascade delete: leads, outreach_steps, replies, sequences
    lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]
    if lead_ids:
        await db.outreach_steps.delete_many({"lead_id": {"$in": lead_ids}})
        await db.replies.delete_many({"lead_id": {"$in": lead_ids}})
    await db.leads.delete_many({"campaign_id": campaign_id})
    await db.sequences.delete_many({"campaign_id": campaign_id})
    await db.campaigns.delete_one({"_id": campaign_id})
    return {"message": "Campaign deleted"}
