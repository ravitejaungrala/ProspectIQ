from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from database import get_db
from models import new_sequence, new_outreach_step, doc_to_dict
from schemas import OutreachStepOut, SequenceOut
from services.ai_service import personalize_email, generate_linkedin_message
from services.email_templates import classify_role, build_email_html, get_subject_line, ROLE_CATEGORIES
from services.email_sender import send_step, send_campaign_approved

router = APIRouter(prefix="/api/outreach", tags=["outreach"])

# Default sequence template — Cold → 3 day follow up → 10 day breakup
DEFAULT_SEQUENCE = [
    {"day": 0, "type": "cold_email", "label": "Day 0 — Cold Email"},
    {"day": 3, "type": "follow_up", "label": "Day 3 — Follow-Up"},
    {"day": 7, "type": "follow_up", "label": "Day 7 — Fresh Angle"},
    {"day": 10, "type": "follow_up", "label": "Day 10 — Final Follow-Up"},
    {"day": 15, "type": "breakup", "label": "Day 15 — Breakup (Final)"},
    {"day": 16, "type": "linkedin", "label": "LinkedIn Message"},
]


@router.post("/campaign/{campaign_id}/enroll")
async def enroll_leads(campaign_id: str):
    """Stage 4: Enroll clean leads in sequence and generate personalized emails."""
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Create default sequence if none exists
    sequence = await db.sequences.find_one({"campaign_id": campaign_id})
    if not sequence:
        seq_doc = new_sequence(campaign_id, "Default Sequence", DEFAULT_SEQUENCE)
        await db.sequences.insert_one(seq_doc)

    # Get clean leads
    leads = await db.leads.find({"campaign_id": campaign_id, "status": "clean"}).to_list(500)

    product_info = {
        "product_name": campaign.get("product_name", ""),
        "product_summary": campaign.get("product_summary", ""),
        "pain_points": campaign.get("pain_points", []),
    }

    enrolled_count = 0
    for lead in leads:
        lead_info = {
            "first_name": lead["first_name"],
            "last_name": lead["last_name"],
            "title": lead["title"],
            "company": lead["company"],
        }

        now = datetime.utcnow()

        for step_def in DEFAULT_SEQUENCE:
            if step_def["type"] == "linkedin":
                try:
                    body = await generate_linkedin_message(lead_info, product_info)
                except Exception:
                    body = f"Hi {lead['first_name']}, I'd love to connect regarding {campaign.get('product_name', '')}."

                step_doc = new_outreach_step(
                    lead_id=lead["_id"],
                    step_number=step_def["day"],
                    step_type="linkedin",
                    template_type="linkedin",
                    subject="LinkedIn Message",
                    body=body,
                    status="pending",
                    scheduled_at=now + timedelta(days=step_def["day"]),
                )
            else:
                try:
                    email_content = await personalize_email(
                        lead_info, product_info, step_def["type"], campaign=campaign,
                    )
                except Exception:
                    email_content = {
                        "subject": f"Quick question, {lead['first_name']}",
                        "body": f"Hi {lead['first_name']},\n\nI wanted to reach out about {campaign.get('product_name', '')}.\n\nBest regards",
                        "html_body": "",
                        "role_category": "general",
                        "template_type": step_def["type"],
                    }

                step_doc = new_outreach_step(
                    lead_id=lead["_id"],
                    step_number=step_def["day"],
                    step_type="email",
                    template_type=email_content.get("template_type", step_def["type"]),
                    role_category=email_content.get("role_category", "general"),
                    subject=email_content.get("subject", ""),
                    body=email_content.get("body", ""),
                    html_body=email_content.get("html_body", ""),
                    status="pending",
                    scheduled_at=now + timedelta(days=step_def["day"]),
                )

            await db.outreach_steps.insert_one(step_doc)

        await db.leads.update_one(
            {"_id": lead["_id"]},
            {"$set": {"status": "enrolled", "updated_at": datetime.utcnow()}},
        )
        enrolled_count += 1

    await db.campaigns.update_one(
        {"_id": campaign_id},
        {"$set": {"status": "active", "updated_at": datetime.utcnow()}},
    )

    return {"message": f"Enrolled {enrolled_count} leads in sequence", "enrolled": enrolled_count}


@router.patch("/step/{step_id}/approve")
async def approve_step(step_id: str):
    """Approve a draft email step for sending."""
    db = get_db()
    step = await db.outreach_steps.find_one({"_id": step_id})
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    await db.outreach_steps.update_one(
        {"_id": step_id},
        {"$set": {"approved": True, "status": "approved"}},
    )
    return {"message": "Step approved for sending"}


@router.patch("/campaign/{campaign_id}/approve-all")
async def approve_all_steps(campaign_id: str):
    """Approve all pending email steps for a campaign."""
    db = get_db()
    lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]
    if not lead_ids:
        raise HTTPException(status_code=404, detail="No leads found")
    result = await db.outreach_steps.update_many(
        {"lead_id": {"$in": lead_ids}, "status": "pending"},
        {"$set": {"approved": True, "status": "approved"}},
    )
    return {"message": f"Approved {result.modified_count} steps", "approved": result.modified_count}


@router.get("/campaign/{campaign_id}/steps", response_model=list[OutreachStepOut])
async def get_campaign_outreach(campaign_id: str):
    db = get_db()
    # Get all lead IDs for this campaign
    lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]
    if not lead_ids:
        return []
    steps = await db.outreach_steps.find(
        {"lead_id": {"$in": lead_ids}}
    ).sort("scheduled_at", 1).to_list(2000)
    return [doc_to_dict(s) for s in steps]


@router.get("/lead/{lead_id}/steps", response_model=list[OutreachStepOut])
async def get_lead_outreach(lead_id: str):
    db = get_db()
    steps = await db.outreach_steps.find(
        {"lead_id": lead_id}
    ).sort("step_number", 1).to_list(100)
    return [doc_to_dict(s) for s in steps]


@router.patch("/step/{step_id}/send")
async def send_single_step(step_id: str):
    """Send a single outreach email via Resend."""
    result = await send_step(step_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/campaign/{campaign_id}/send")
async def send_campaign_emails(campaign_id: str, batch_size: int = 50):
    """Send all approved & due email steps for a campaign via Resend."""
    db = get_db()
    campaign = await db.campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await send_campaign_approved(campaign_id, batch_size)


@router.get("/sequence/{campaign_id}", response_model=SequenceOut)
async def get_sequence(campaign_id: str):
    db = get_db()
    seq = await db.sequences.find_one({"campaign_id": campaign_id})
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return doc_to_dict(seq)


@router.get("/step/{step_id}/preview", response_class=HTMLResponse)
async def preview_step_html(step_id: str):
    """Return the HTML body of an outreach step for preview."""
    db = get_db()
    step = await db.outreach_steps.find_one({"_id": step_id})
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    html = step.get("html_body", "")
    if not html:
        return HTMLResponse(f"<html><body><pre>{step.get('body', 'No content')}</pre></body></html>")
    return HTMLResponse(html)


@router.get("/templates/preview")
async def preview_template(
    template_type: str = "cold_email",
    role_category: str = "ceo",
    campaign_id: str = None,
):
    """Preview a template with sample data. Optionally use a real campaign's info."""
    # Default sample data
    first_name = "Alex"
    company = "Acme Corp"
    title = "CEO"
    product_name = "ProspectIQ"
    product_summary = "AI-powered lead generation and outreach platform that finds, scores, and engages your ideal prospects automatically."
    product_url = "https://prospectiq.ai"
    pain_points = ["manual lead research", "low response rates", "inconsistent outreach"]
    demo_video_url = ""
    sender_name = "Sarah Johnson"
    sender_title = "Growth Lead"
    sender_phone = "+1 (555) 123-4567"

    if campaign_id:
        db = get_db()
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if campaign:
            product_name = campaign.get("product_name", product_name)
            product_summary = campaign.get("product_summary", product_summary)
            product_url = campaign.get("product_url", product_url)
            pain_points = campaign.get("pain_points", pain_points)
            demo_video_url = campaign.get("demo_video_url", "")
            sender_name = campaign.get("sender_name", sender_name)
            sender_title = campaign.get("sender_title", sender_title)
            sender_phone = campaign.get("sender_phone", sender_phone)

    subject = get_subject_line(
        template_type, role_category,
        first_name, company, product_name, sender_name, pain_points,
    )

    sample_body = (
        f"I noticed {company} has been scaling rapidly — congratulations on the growth.\n\n"
        f"Teams in your space often struggle with {pain_points[0] if pain_points else 'outreach efficiency'}. "
        f"That's exactly what {product_name} solves.\n\n"
        f"We helped a similar company reduce their prospecting time by 70% while tripling response rates.\n\n"
        f"Would it make sense to explore how this maps to {company}'s goals? Happy to share a quick 15-min walkthrough."
    )

    html = build_email_html(
        template_type=template_type,
        ai_body=sample_body,
        subject=subject,
        first_name=first_name,
        company=company,
        title=title,
        product_name=product_name,
        product_summary=product_summary,
        product_url=product_url,
        pain_points=pain_points,
        demo_video_url=demo_video_url,
        sender_name=sender_name,
        sender_title=sender_title,
        sender_phone=sender_phone,
        role_category=role_category,
    )

    return HTMLResponse(html)


@router.get("/templates/types")
async def list_template_types():
    """Return available template types and role categories."""
    return {
        "template_types": [
            {"id": "cold_email", "label": "Cold Email", "description": "First outreach — personalized hook + CTA"},
            {"id": "follow_up", "label": "Follow-Up", "description": "Fresh angle, new data, case study"},
            {"id": "introduction", "label": "Introduction", "description": "Warm intro from sender"},
            {"id": "breakup", "label": "Breakup", "description": "Final short touchpoint — highest reply rate"},
        ],
        "role_categories": [
            {"id": "ceo", "label": "CEO / Founder", "description": "Strategic ROI, market position"},
            {"id": "cto", "label": "CTO / Engineering", "description": "Technical credibility, integrations"},
            {"id": "manager", "label": "Manager / Director", "description": "Team productivity, KPIs"},
            {"id": "hr", "label": "HR / People Ops", "description": "Compliance, admin reduction"},
            {"id": "marketing", "label": "Marketing", "description": "Growth metrics, conversion"},
            {"id": "sales", "label": "Sales", "description": "Pipeline velocity, revenue"},
            {"id": "employee", "label": "Employee / IC", "description": "Daily ease of use"},
            {"id": "general", "label": "General", "description": "Balanced professional tone"},
        ],
    }
