from fastapi import APIRouter
from database import get_db
from schemas import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    db = get_db()
    total_campaigns = await db.campaigns.count_documents({})
    active_campaigns = await db.campaigns.count_documents({"status": {"$in": ["active", "outreach"]}})
    total_leads = await db.leads.count_documents({})
    verified_leads = await db.leads.count_documents({"email_status": "valid"})
    emails_sent = await db.outreach_steps.count_documents({"status": "sent"})
    emails_opened = await db.outreach_steps.count_documents({"opened_at": {"$ne": None}})
    replies_received = await db.replies.count_documents({})
    interested_replies = await db.replies.count_documents({"intent": "interested"})
    demos_booked = await db.replies.count_documents({"intent": "demo"})

    open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
    reply_rate = (replies_received / emails_sent * 100) if emails_sent > 0 else 0
    interest_rate = (interested_replies / replies_received * 100) if replies_received > 0 else 0

    return DashboardStats(
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_leads=total_leads,
        verified_leads=verified_leads,
        emails_sent=emails_sent,
        emails_opened=emails_opened,
        replies_received=replies_received,
        interested_replies=interested_replies,
        demos_booked=demos_booked,
        open_rate=round(open_rate, 1),
        reply_rate=round(reply_rate, 1),
        interest_rate=round(interest_rate, 1),
    )
