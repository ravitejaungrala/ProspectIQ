from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from database import get_db
from models import doc_to_dict

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/campaign/{campaign_id}")
async def get_campaign_analytics(campaign_id: str):
    """Full analytics for a specific campaign."""
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]

    total_leads = len(lead_ids)
    if not lead_ids:
        return _empty_analytics(campaign)

    # Outreach step stats
    all_steps = await db.outreach_steps.find({"lead_id": {"$in": lead_ids}}).to_list(5000)

    email_steps = [s for s in all_steps if s.get("step_type") == "email"]
    linkedin_steps = [s for s in all_steps if s.get("step_type") == "linkedin"]

    total_emails = len(email_steps)
    approved = len([s for s in email_steps if s.get("approved")])
    sent = len([s for s in email_steps if s.get("status") == "sent"])
    opened = len([s for s in email_steps if s.get("opened_at")])
    clicked = len([s for s in email_steps if s.get("clicked_at")])
    replied = len([s for s in email_steps if s.get("replied_at")])
    pending = len([s for s in email_steps if s.get("status") == "pending"])

    # By template type
    by_type = {}
    for s in email_steps:
        t = s.get("template_type", "unknown")
        if t not in by_type:
            by_type[t] = {"total": 0, "sent": 0, "opened": 0, "clicked": 0, "replied": 0}
        by_type[t]["total"] += 1
        if s.get("status") == "sent":
            by_type[t]["sent"] += 1
        if s.get("opened_at"):
            by_type[t]["opened"] += 1
        if s.get("clicked_at"):
            by_type[t]["clicked"] += 1
        if s.get("replied_at"):
            by_type[t]["replied"] += 1

    # By role category
    by_role = {}
    for s in email_steps:
        r = s.get("role_category", "general")
        if r not in by_role:
            by_role[r] = {"total": 0, "sent": 0, "opened": 0, "replied": 0}
        by_role[r]["total"] += 1
        if s.get("status") == "sent":
            by_role[r]["sent"] += 1
        if s.get("opened_at"):
            by_role[r]["opened"] += 1
        if s.get("replied_at"):
            by_role[r]["replied"] += 1

    # Sequence progress — how many leads at each step
    sequence_progress = {}
    for s in email_steps:
        step_num = s.get("step_number", 0)
        label = s.get("template_type", f"day_{step_num}")
        if label not in sequence_progress:
            sequence_progress[label] = {"pending": 0, "approved": 0, "sent": 0, "replied": 0}
        status = s.get("status", "pending")
        if status in sequence_progress[label]:
            sequence_progress[label][status] += 1
        if s.get("replied_at"):
            sequence_progress[label]["replied"] += 1

    # Replies analysis
    replies = await db.replies.find({"lead_id": {"$in": lead_ids}}).to_list(500)
    intent_breakdown = {}
    for r in replies:
        intent = r.get("intent", "unknown")
        intent_breakdown[intent] = intent_breakdown.get(intent, 0) + 1

    # Timeline — emails sent per day (last 30 days)
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    daily_sent = {}
    for s in email_steps:
        if s.get("sent_at") and s["sent_at"] >= thirty_days_ago:
            day = s["sent_at"].strftime("%Y-%m-%d")
            daily_sent[day] = daily_sent.get(day, 0) + 1

    # Lead statuses
    lead_statuses = {}
    async for lead in db.leads.find({"campaign_id": campaign_id}):
        st = lead.get("status", "raw")
        lead_statuses[st] = lead_statuses.get(st, 0) + 1

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.get("product_name", ""),
        "overview": {
            "total_leads": total_leads,
            "total_emails": total_emails,
            "pending": pending,
            "approved": approved,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "open_rate": round(opened / sent * 100, 1) if sent else 0,
            "click_rate": round(clicked / sent * 100, 1) if sent else 0,
            "reply_rate": round(replied / sent * 100, 1) if sent else 0,
            "approval_rate": round(approved / total_emails * 100, 1) if total_emails else 0,
        },
        "by_template_type": by_type,
        "by_role": by_role,
        "sequence_progress": sequence_progress,
        "lead_statuses": lead_statuses,
        "intent_breakdown": intent_breakdown,
        "total_replies": len(replies),
        "daily_sent": daily_sent,
        "linkedin_steps": len(linkedin_steps),
    }


@router.get("/overview")
async def get_global_analytics():
    """Global analytics across all campaigns."""
    db = get_db()

    total_campaigns = await db.campaigns.count_documents({})
    active_campaigns = await db.campaigns.count_documents({"status": {"$in": ["active", "outreach"]}})
    total_leads = await db.leads.count_documents({})

    # Global email stats
    total_sent = await db.outreach_steps.count_documents({"status": "sent", "step_type": "email"})
    total_opened = await db.outreach_steps.count_documents({"opened_at": {"$ne": None}, "step_type": "email"})
    total_clicked = await db.outreach_steps.count_documents({"clicked_at": {"$ne": None}, "step_type": "email"})
    total_replied = await db.outreach_steps.count_documents({"replied_at": {"$ne": None}, "step_type": "email"})
    total_pending = await db.outreach_steps.count_documents({"status": "pending", "step_type": "email"})
    total_approved = await db.outreach_steps.count_documents({"status": "approved", "step_type": "email"})

    # Replies
    total_replies = await db.replies.count_documents({})
    interested = await db.replies.count_documents({"intent": "interested"})
    demos = await db.replies.count_documents({"intent": "demo"})
    not_interested = await db.replies.count_documents({"intent": "not_interested"})

    # Per-campaign summary
    campaign_summaries = []
    async for c in db.campaigns.find().sort("created_at", -1).limit(20):
        lid = [l["_id"] async for l in db.leads.find({"campaign_id": c["_id"]}, {"_id": 1})]
        c_sent = await db.outreach_steps.count_documents({"lead_id": {"$in": lid}, "status": "sent"}) if lid else 0
        c_replied = await db.outreach_steps.count_documents({"lead_id": {"$in": lid}, "replied_at": {"$ne": None}}) if lid else 0
        campaign_summaries.append({
            "id": c["_id"],
            "name": c.get("product_name", ""),
            "status": c.get("status", ""),
            "leads": len(lid),
            "sent": c_sent,
            "replied": c_replied,
            "reply_rate": round(c_replied / c_sent * 100, 1) if c_sent else 0,
        })

    return {
        "total_campaigns": total_campaigns,
        "active_campaigns": active_campaigns,
        "total_leads": total_leads,
        "emails": {
            "pending": total_pending,
            "approved": total_approved,
            "sent": total_sent,
            "opened": total_opened,
            "clicked": total_clicked,
            "replied": total_replied,
            "open_rate": round(total_opened / total_sent * 100, 1) if total_sent else 0,
            "click_rate": round(total_clicked / total_sent * 100, 1) if total_sent else 0,
            "reply_rate": round(total_replied / total_sent * 100, 1) if total_sent else 0,
        },
        "replies": {
            "total": total_replies,
            "interested": interested,
            "demos": demos,
            "not_interested": not_interested,
        },
        "campaigns": campaign_summaries,
    }


@router.get("/campaign/{campaign_id}/leads-activity")
async def get_leads_activity(campaign_id: str):
    """Per-lead outreach activity for a campaign."""
    db = get_db()
    leads = await db.leads.find({"campaign_id": campaign_id}).to_list(500)
    result = []
    for lead in leads:
        steps = await db.outreach_steps.find({"lead_id": lead["_id"]}).sort("step_number", 1).to_list(20)
        step_summary = []
        for s in steps:
            step_summary.append({
                "step_number": s.get("step_number"),
                "template_type": s.get("template_type", ""),
                "status": s.get("status"),
                "approved": s.get("approved", False),
                "sent_at": s.get("sent_at"),
                "opened_at": s.get("opened_at"),
                "replied_at": s.get("replied_at"),
            })
        result.append({
            "lead_id": lead["_id"],
            "name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}",
            "email": lead.get("email", ""),
            "company": lead.get("company", ""),
            "title": lead.get("title", ""),
            "status": lead.get("status", ""),
            "steps": step_summary,
        })
    return result


def _empty_analytics(campaign: dict) -> dict:
    return {
        "campaign_id": campaign["_id"],
        "campaign_name": campaign.get("product_name", ""),
        "overview": {
            "total_leads": 0, "total_emails": 0, "pending": 0, "approved": 0,
            "sent": 0, "opened": 0, "clicked": 0, "replied": 0,
            "open_rate": 0, "click_rate": 0, "reply_rate": 0, "approval_rate": 0,
        },
        "by_template_type": {},
        "by_role": {},
        "sequence_progress": {},
        "lead_statuses": {},
        "intent_breakdown": {},
        "total_replies": 0,
        "daily_sent": {},
        "linkedin_steps": 0,
    }
