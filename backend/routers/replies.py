from fastapi import APIRouter, HTTPException
from database import get_db
from models import new_reply, new_suppression, doc_to_dict
from schemas import ReplyOut, ReplyCreate
from services.ai_service import classify_reply_intent, draft_reply

router = APIRouter(prefix="/api/replies", tags=["replies"])


@router.post("", response_model=ReplyOut)
async def handle_incoming_reply(data: ReplyCreate):
    """Stage 5: Handle an incoming reply — classify intent and draft response."""
    db = get_db()
    lead = await db.leads.find_one({"_id": data.lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    campaign = await db.campaigns.find_one({"_id": lead["campaign_id"]})
    product_info = {
        "product_name": campaign.get("product_name", "") if campaign else "",
        "product_summary": campaign.get("product_summary", "") if campaign else "",
    }

    # Classify intent
    try:
        intent = await classify_reply_intent(data.body)
    except Exception:
        intent = "question"

    # Draft AI reply
    try:
        ai_draft = await draft_reply(data.body, intent, product_info)
    except Exception:
        ai_draft = ""

    reply_doc = new_reply(
        lead_id=data.lead_id,
        from_email=data.from_email,
        subject=data.subject,
        body=data.body,
        intent=intent,
        ai_draft_reply=ai_draft,
    )
    await db.replies.insert_one(reply_doc)

    # Update lead status based on intent
    lead_updates = {"status": "replied"}

    if intent in ("unsubscribe", "not_interested"):
        # Add to suppression list
        existing = await db.suppression_list.find_one({"email": lead["email"]})
        if not existing:
            await db.suppression_list.insert_one(new_suppression(lead["email"], intent))
        lead_updates["is_suppressed"] = True
        lead_updates["suppression_reason"] = intent
    elif intent in ("interested", "demo"):
        lead_updates["status"] = "converted"

    from datetime import datetime
    lead_updates["updated_at"] = datetime.utcnow()
    await db.leads.update_one({"_id": data.lead_id}, {"$set": lead_updates})

    return doc_to_dict(reply_doc)


@router.get("/campaign/{campaign_id}", response_model=list[ReplyOut])
async def get_campaign_replies(campaign_id: str):
    db = get_db()
    lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]
    if not lead_ids:
        return []
    replies = await db.replies.find(
        {"lead_id": {"$in": lead_ids}}
    ).sort("received_at", -1).to_list(500)
    return [doc_to_dict(r) for r in replies]


@router.get("", response_model=list[ReplyOut])
async def get_all_replies():
    db = get_db()
    replies = await db.replies.find().sort("received_at", -1).to_list(100)
    return [doc_to_dict(r) for r in replies]


@router.patch("/{reply_id}/handle")
async def mark_reply_handled(reply_id: str):
    db = get_db()
    result = await db.replies.update_one(
        {"_id": reply_id},
        {"$set": {"is_handled": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reply not found")
    return {"message": "Reply marked as handled"}
