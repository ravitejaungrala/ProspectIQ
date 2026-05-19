from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db
from models import doc_to_dict
from services.agents import ReplyAgent, MailAgent, PerformanceAgent, ContextAgent

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ─── Schemas ─────────────────────────────────────────────────────
class IncomingReply(BaseModel):
    campaign_id: str
    lead_id: str
    from_email: str
    subject: str
    body: str


class QuestionRequest(BaseModel):
    question: str


# ─── Reply Agent ─────────────────────────────────────────────────
@router.post("/reply/process")
async def process_reply(data: IncomingReply):
    """Reply Agent: classify intent, generate smart response, execute actions."""
    result = await ReplyAgent.process_reply(
        campaign_id=data.campaign_id,
        lead_id=data.lead_id,
        reply_body=data.body,
        from_email=data.from_email,
        subject=data.subject,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/reply/classify")
async def classify_reply(data: dict):
    """Quick intent classification without full processing."""
    body = data.get("body", "")
    if not body:
        raise HTTPException(status_code=400, detail="body required")
    return await ReplyAgent.classify_intent(body)


# ─── Mail Agent ──────────────────────────────────────────────────
@router.get("/mail/campaign/{campaign_id}/pending")
async def get_pending_sends(campaign_id: str):
    """Get all approved but unsent steps for a campaign."""
    steps = await MailAgent.get_pending_sends(campaign_id)
    return [doc_to_dict(s) for s in steps]


@router.get("/mail/campaign/{campaign_id}/no-reply")
async def get_no_reply_leads(campaign_id: str, days: int = 3):
    """Find leads who haven't replied after X days."""
    return await MailAgent.get_no_reply_leads(campaign_id, days)


@router.post("/mail/campaign/{campaign_id}/auto-advance")
async def auto_advance_sequence(campaign_id: str):
    """Auto-advance no-reply leads to their next sequence step."""
    return await MailAgent.auto_send_next(campaign_id)


@router.get("/mail/campaign/{campaign_id}/status")
async def mail_status(campaign_id: str):
    """Get mail pipeline status overview."""
    return await MailAgent.get_campaign_mail_status(campaign_id)


# ─── Performance Agent ───────────────────────────────────────────
@router.get("/performance/campaign/{campaign_id}")
async def analyze_performance(campaign_id: str):
    """Full AI performance analysis with recommendations."""
    return await PerformanceAgent.analyze_campaign(campaign_id)


# ─── Context Agent ───────────────────────────────────────────────
@router.post("/context/campaign/{campaign_id}/build")
async def build_context(campaign_id: str):
    """Build comprehensive business context for a campaign."""
    return await ContextAgent.build_context(campaign_id)


@router.get("/context/campaign/{campaign_id}")
async def get_context(campaign_id: str):
    """Get stored business context."""
    return await ContextAgent.get_context(campaign_id)


@router.post("/context/campaign/{campaign_id}/ask")
async def ask_question(campaign_id: str, data: QuestionRequest):
    """Ask the Context Agent a question about the product."""
    answer = await ContextAgent.answer_question(campaign_id, data.question)
    return {"answer": answer}


# ─── Agent Logs ──────────────────────────────────────────────────
@router.get("/logs/campaign/{campaign_id}")
async def get_agent_logs(campaign_id: str, limit: int = 50):
    """Get recent agent activity logs for a campaign."""
    db = get_db()
    logs = await db.agent_logs.find(
        {"campaign_id": campaign_id}
    ).sort("created_at", -1).to_list(limit)
    return [doc_to_dict(l) for l in logs]


@router.get("/logs")
async def get_all_agent_logs(limit: int = 100):
    """Get all recent agent activity logs."""
    db = get_db()
    logs = await db.agent_logs.find().sort("created_at", -1).to_list(limit)
    return [doc_to_dict(l) for l in logs]


# ─── Agent Overview ──────────────────────────────────────────────
@router.get("/overview/campaign/{campaign_id}")
async def agent_overview(campaign_id: str):
    """Get a summary of all agent statuses for a campaign."""
    db = get_db()

    mail_status = await MailAgent.get_campaign_mail_status(campaign_id)
    no_reply = await MailAgent.get_no_reply_leads(campaign_id)

    # Reply stats
    lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]
    replies = await db.replies.find({"lead_id": {"$in": lead_ids}}).to_list(500)
    intent_counts = {}
    for r in replies:
        intent = r.get("intent", "unknown")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    # Context status
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    has_context = bool(campaign and campaign.get("business_context"))

    # Recent logs
    recent_logs = await db.agent_logs.find(
        {"campaign_id": campaign_id}
    ).sort("created_at", -1).to_list(10)

    return {
        "mail_agent": {
            "status": "active",
            **mail_status,
            "no_reply_count": len(no_reply),
        },
        "reply_agent": {
            "status": "active",
            "total_replies": len(replies),
            "intent_breakdown": intent_counts,
            "unhandled": len([r for r in replies if not r.get("is_handled", False)]),
        },
        "performance_agent": {
            "status": "active",
            "total_sent": mail_status.get("sent", 0),
            "reply_rate": round(
                (len(replies) / mail_status["sent"] * 100)
                if mail_status.get("sent", 0) > 0 else 0, 1
            ),
        },
        "context_agent": {
            "status": "ready" if has_context else "not_built",
            "has_context": has_context,
        },
        "recent_logs": [doc_to_dict(l) for l in recent_logs],
    }
