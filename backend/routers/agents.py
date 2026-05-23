from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import doc_to_dict
from services.agents import (
    ReplyAgent, MailAgent, PerformanceAgent, ContextAgent,
    ResearchAgent, LeadIdentificationAgent, PersonalizationAgent,
    OutreachAgent, ResponseHandlingAgent, BookingAgent,
)

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


class BookingConfirmRequest(BaseModel):
    meeting_date: Optional[str] = ""
    meeting_time: Optional[str] = ""
    meeting_link: Optional[str] = ""
    notes: Optional[str] = ""


class BookingLinkRequest(BaseModel):
    custom_message: Optional[str] = ""


class AutoRespondRequest(BaseModel):
    auto_send_low_risk: Optional[bool] = False


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

    # Booking stats
    booking_pipeline = await BookingAgent.get_booking_pipeline(campaign_id)
    funnel = booking_pipeline.get("funnel", {})

    # Research stats
    researched_count = await db.leads.count_documents({
        "campaign_id": campaign_id,
        "research_data": {"$exists": True}
    })
    total_leads = await db.leads.count_documents({"campaign_id": campaign_id})

    # Personalization stats
    personalized_count = await db.outreach_steps.count_documents({
        "lead_id": {"$in": lead_ids},
        "is_personalized": True
    })

    # Recent logs
    recent_logs = await db.agent_logs.find(
        {"campaign_id": campaign_id}
    ).sort("created_at", -1).to_list(10)

    return {
        # Legacy agents (kept for backward compat)
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
        # New agents
        "research_agent": {
            "status": "active",
            "researched": researched_count,
            "total_leads": total_leads,
            "pending": max(0, total_leads - researched_count),
        },
        "kp_agent": {
            "status": "active",
            "total_leads": total_leads,
            "scored": await db.leads.count_documents({
                "campaign_id": campaign_id, "profile_score": {"$gt": 0}
            }),
        },
        "personalization_agent": {
            "status": "active",
            "personalized": personalized_count,
            "pending": await db.outreach_steps.count_documents({
                "lead_id": {"$in": lead_ids},
                "is_personalized": {"$ne": True},
                "status": {"$in": ["pending", "approved"]},
            }),
        },
        "outreach_agent": {
            "status": "active",
            **mail_status,
            "no_reply_count": len(no_reply),
        },
        "response_handling_agent": {
            "status": "active",
            "total_replies": len(replies),
            "unhandled": len([r for r in replies if not r.get("is_handled", False)]),
            "intent_breakdown": intent_counts,
        },
        "booking_agent": {
            "status": "active",
            "hot_leads": funnel.get("interested", 0),
            "booked": funnel.get("booked", 0),
            "converted": funnel.get("converted", 0),
            "booking_rate": booking_pipeline.get("booking_rate", 0),
        },
        "recent_logs": [doc_to_dict(l) for l in recent_logs],
    }


# ─── Research Agent ──────────────────────────────────────────────
@router.post("/research/campaign/{campaign_id}/all")
async def research_all_leads(campaign_id: str):
    """Research Agent: batch-research all unresearched leads."""
    return await ResearchAgent.research_all_leads(campaign_id)


@router.post("/research/lead/{lead_id}")
async def research_lead(lead_id: str):
    """Research Agent: deep-research a single lead."""
    result = await ResearchAgent.research_lead(lead_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/research/lead/{lead_id}/hooks")
async def get_lead_hooks(lead_id: str):
    """Research Agent: get personalization hooks for a lead."""
    hooks = await ResearchAgent.generate_hooks_for_lead(lead_id)
    return {"hooks": hooks}


@router.post("/research/company")
async def research_company(data: dict):
    """Research Agent: research a company by domain."""
    domain = data.get("domain", "")
    if not domain:
        raise HTTPException(status_code=400, detail="domain required")
    return await ResearchAgent.research_company(domain)


# ─── Lead Identification Agent (KP) ─────────────────────────────
@router.post("/kp/campaign/{campaign_id}/score")
async def score_leads(campaign_id: str):
    """KP Agent: score and rank all leads by ICP fit."""
    return await LeadIdentificationAgent.score_and_rank_leads(campaign_id)


@router.get("/kp/campaign/{campaign_id}/key-persons")
async def get_key_persons(campaign_id: str):
    """KP Agent: identify the best contact at each company."""
    return await LeadIdentificationAgent.identify_key_persons(campaign_id)


@router.get("/kp/campaign/{campaign_id}/best-contact")
async def get_best_contact(campaign_id: str, domain: str):
    """KP Agent: find best contact at a specific domain."""
    result = await LeadIdentificationAgent.find_best_contact(campaign_id, domain)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/kp/campaign/{campaign_id}/flag-weak")
async def flag_weak_leads(campaign_id: str, threshold: float = 30.0):
    """KP Agent: flag leads with low ICP scores."""
    return await LeadIdentificationAgent.flag_weak_leads(campaign_id, threshold)


# ─── Personalization Agent ───────────────────────────────────────
@router.post("/personalization/campaign/{campaign_id}/batch")
async def batch_personalize(campaign_id: str):
    """Personalization Agent: personalize all pending emails in a campaign."""
    return await PersonalizationAgent.batch_personalize(campaign_id)


@router.post("/personalization/step/{step_id}")
async def personalize_step(step_id: str):
    """Personalization Agent: personalize a specific outreach step."""
    result = await PersonalizationAgent.personalize_step(step_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/personalization/lead/{lead_id}/preview")
async def preview_personalization(lead_id: str, campaign_id: str):
    """Personalization Agent: preview personalized email for a lead."""
    result = await PersonalizationAgent.preview_personalization(lead_id, campaign_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/personalization/lead/{lead_id}/opening-line")
async def get_opening_line(lead_id: str, campaign_id: str):
    """Personalization Agent: generate a personalized opening line."""
    line = await PersonalizationAgent.generate_opening_line(lead_id, campaign_id)
    return {"opening_line": line}


# ─── Outreach Agent ──────────────────────────────────────────────
@router.get("/outreach/campaign/{campaign_id}/queue")
async def get_send_queue(campaign_id: str):
    """Outreach Agent: get the prioritized send queue."""
    return await OutreachAgent.get_send_queue(campaign_id)


@router.post("/outreach/campaign/{campaign_id}/batch-send")
async def batch_approve_and_send(campaign_id: str, high_priority_only: bool = False):
    """Outreach Agent: approve and send all pending emails."""
    return await OutreachAgent.batch_approve_and_send(campaign_id, high_priority_only)


@router.post("/outreach/campaign/{campaign_id}/run-pipeline")
async def run_full_pipeline(campaign_id: str):
    """Outreach Agent: run the complete outreach pipeline end-to-end."""
    return await OutreachAgent.run_full_pipeline(campaign_id)


@router.get("/outreach/campaign/{campaign_id}/stats")
async def get_outreach_stats(campaign_id: str):
    """Outreach Agent: real-time outreach stats."""
    return await OutreachAgent.get_outreach_stats(campaign_id)


# ─── Response Handling Agent ─────────────────────────────────────
@router.get("/response/campaign/{campaign_id}/queue")
async def get_response_queue(campaign_id: str):
    """Response Handling Agent: get the triaged reply queue."""
    return await ResponseHandlingAgent.get_response_queue(campaign_id)


@router.post("/response/reply/{reply_id}/auto-respond")
async def auto_respond(reply_id: str):
    """Response Handling Agent: auto-send the AI draft response."""
    result = await ResponseHandlingAgent.auto_respond(reply_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/response/campaign/{campaign_id}/handle-all")
async def handle_all_unhandled(campaign_id: str, data: AutoRespondRequest = AutoRespondRequest()):
    """Response Handling Agent: process all unhandled replies."""
    return await ResponseHandlingAgent.handle_all_unhandled(
        campaign_id, auto_send_low_risk=data.auto_send_low_risk
    )


# ─── Booking Agent ───────────────────────────────────────────────
@router.get("/booking/campaign/{campaign_id}/hot-leads")
async def get_hot_leads(campaign_id: str):
    """Booking Agent: get leads showing strong buying / booking intent."""
    return await BookingAgent.get_hot_leads(campaign_id)


@router.post("/booking/lead/{lead_id}/send-link")
async def send_booking_link(lead_id: str, campaign_id: str, data: BookingLinkRequest = BookingLinkRequest()):
    """Booking Agent: send a booking link to an interested lead."""
    result = await BookingAgent.send_booking_link(lead_id, campaign_id, data.custom_message or "")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/booking/lead/{lead_id}/confirm")
async def confirm_booking(lead_id: str, campaign_id: str, data: BookingConfirmRequest = BookingConfirmRequest()):
    """Booking Agent: confirm a meeting has been booked."""
    meeting_info = {
        "date": data.meeting_date,
        "time": data.meeting_time,
        "link": data.meeting_link,
        "notes": data.notes,
    }
    return await BookingAgent.confirm_booking(lead_id, campaign_id, meeting_info)


@router.post("/booking/campaign/{campaign_id}/follow-up")
async def follow_up_unbooked(campaign_id: str):
    """Booking Agent: follow up with interested leads who haven't booked."""
    return await BookingAgent.follow_up_unbooked(campaign_id)


@router.get("/booking/campaign/{campaign_id}/pipeline")
async def get_booking_pipeline(campaign_id: str):
    """Booking Agent: get the full booking funnel stats."""
    return await BookingAgent.get_booking_pipeline(campaign_id)
