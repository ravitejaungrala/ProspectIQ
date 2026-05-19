"""
Email sending service via SMTP (Gmail).
Handles actual delivery of outreach emails.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from database import get_db
from config import get_settings


def _get_smtp_connection():
    """Create and return an authenticated SMTP connection."""
    settings = get_settings()
    server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
    server.starttls()
    server.login(settings.smtp_user, settings.smtp_password)
    return server


async def send_email(to_email: str, subject: str, html_body: str, from_email: str = None, from_name: str = None) -> dict:
    """Send a single email via SMTP. Returns status dict."""
    settings = get_settings()

    if not settings.smtp_user or not settings.smtp_password:
        return {"error": "SMTP credentials not configured in .env"}

    # Build the email
    msg = MIMEMultipart("alternative")
    sender_name = from_name or settings.smtp_from_name or "ProspectIQ"
    sender_email = settings.smtp_user  # Gmail requires sending from the authenticated account
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    # Reply-To can be the campaign sender's email if different
    if from_email and from_email != sender_email:
        msg["Reply-To"] = f"{from_name} <{from_email}>" if from_name else from_email

    # Attach plain text fallback + HTML
    plain_text = html_body.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    # Strip HTML tags for plain text
    import re
    plain_text = re.sub(r"<[^>]+>", "", plain_text)
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = _get_smtp_connection()
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return {"status": "sent"}
    except smtplib.SMTPAuthenticationError:
        return {"error": "SMTP authentication failed — check your App Password"}
    except smtplib.SMTPRecipientsRefused:
        return {"error": f"Recipient refused: {to_email}"}
    except Exception as e:
        return {"error": str(e)}


async def send_step(step_id: str) -> dict:
    """Send a single outreach step email. Updates status in DB."""
    db = get_db()
    step = await db.outreach_steps.find_one({"_id": step_id})
    if not step:
        return {"error": "Step not found"}

    if step.get("status") == "sent":
        return {"error": "Already sent"}

    if step.get("step_type") == "linkedin":
        return {"error": "LinkedIn messages cannot be sent via email"}

    # Get lead info for the recipient
    lead = await db.leads.find_one({"_id": step["lead_id"]})
    if not lead:
        return {"error": "Lead not found"}

    if not lead.get("email"):
        return {"error": "Lead has no email address"}

    # Get campaign for sender info
    campaign = await db.campaigns.find_one({"_id": lead.get("campaign_id")})
    sender_name = campaign.get("sender_name", "") if campaign else ""
    sender_email = campaign.get("sender_email", "") if campaign else ""

    # Send the email
    html = step.get("html_body") or f"<div style='font-family:sans-serif;line-height:1.7'>{step.get('body', '').replace(chr(10), '<br>')}</div>"
    result = await send_email(
        to_email=lead["email"],
        subject=step.get("subject", ""),
        html_body=html,
        from_email=sender_email,
        from_name=sender_name,
    )

    now = datetime.utcnow()

    if "error" in result:
        # Log failure but don't crash
        await db.outreach_steps.update_one(
            {"_id": step_id},
            {"$set": {"status": "failed", "send_error": result["error"], "updated_at": now}},
        )
        return result

    # Mark as sent
    await db.outreach_steps.update_one(
        {"_id": step_id},
        {"$set": {
            "status": "sent",
            "sent_at": now,
        }},
    )

    # Update lead
    await db.leads.update_one(
        {"_id": lead["_id"]},
        {"$set": {"last_contacted_at": now, "status": "contacted", "updated_at": now}},
    )

    return {"status": "sent", "to": lead["email"]}


async def send_campaign_approved(campaign_id: str, batch_size: int = 50) -> dict:
    """Send all approved (unsent) email steps for a campaign. Returns summary."""
    db = get_db()

    # Get lead IDs for this campaign
    lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]
    if not lead_ids:
        return {"sent": 0, "failed": 0, "errors": [], "message": "No leads found"}

    # Get only approved, unsent email steps that are due (scheduled_at <= now)
    now = datetime.utcnow()
    steps = await db.outreach_steps.find({
        "lead_id": {"$in": lead_ids},
        "status": "approved",
        "step_type": "email",
        "scheduled_at": {"$lte": now},
    }).sort("scheduled_at", 1).to_list(batch_size)

    sent = 0
    failed = 0
    errors = []

    for step in steps:
        result = await send_step(step["_id"])
        if "error" in result:
            failed += 1
            errors.append({"step_id": step["_id"], "error": result["error"]})
        else:
            sent += 1

    return {
        "sent": sent,
        "failed": failed,
        "total_processed": sent + failed,
        "errors": errors,
        "message": f"Sent {sent} emails, {failed} failed",
    }
