"""
MongoDB document factory functions.
Each function returns a dict that represents a document for its collection.
"""
import uuid
from datetime import datetime


def generate_id():
    return str(uuid.uuid4())


def new_campaign(product_url: str) -> dict:
    return {
        "_id": generate_id(),
        "product_url": product_url,
        "product_name": "",
        "product_summary": "",
        "ideal_customer_profile": {},
        "industries": [],
        "roles": [],
        "pain_points": [],
        "demo_video_url": "",
        "calendly_url": "",
        "demo_booking_url": "",
        "product_phone": "",
        "contact_emails": [],
        "social_links": {},
        "target_domains": [],
        "sender_name": "",
        "sender_title": "",
        "sender_email": "",
        "sender_phone": "",
        "status": "setup",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def new_lead(campaign_id: str, **kwargs) -> dict:
    return {
        "_id": generate_id(),
        "campaign_id": campaign_id,
        "first_name": kwargs.get("first_name", ""),
        "last_name": kwargs.get("last_name", ""),
        "email": kwargs.get("email", ""),
        "company": kwargs.get("company", ""),
        "title": kwargs.get("title", ""),
        "linkedin_url": kwargs.get("linkedin_url", ""),
        "domain": kwargs.get("domain", ""),
        "phone": kwargs.get("phone", ""),
        "email_status": "pending",
        "profile_score": 0.0,
        "is_suppressed": False,
        "suppression_reason": "",
        "last_contacted_at": None,
        "pitched_products": [],
        "status": kwargs.get("status", "raw"),
        "drop_reason": "",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def new_sequence(campaign_id: str, name: str = "Default Sequence", steps: list = None) -> dict:
    return {
        "_id": generate_id(),
        "campaign_id": campaign_id,
        "name": name,
        "steps": steps or [],
        "is_active": True,
        "created_at": datetime.utcnow(),
    }


def new_outreach_step(lead_id: str, **kwargs) -> dict:
    return {
        "_id": generate_id(),
        "lead_id": lead_id,
        "step_number": kwargs.get("step_number", 0),
        "step_type": kwargs.get("step_type", "email"),
        "template_type": kwargs.get("template_type", "cold_email"),
        "role_category": kwargs.get("role_category", "general"),
        "subject": kwargs.get("subject", ""),
        "body": kwargs.get("body", ""),
        "html_body": kwargs.get("html_body", ""),
        "status": kwargs.get("status", "pending"),
        "approved": kwargs.get("approved", False),
        "scheduled_at": kwargs.get("scheduled_at"),
        "sent_at": None,
        "opened_at": None,
        "clicked_at": None,
        "replied_at": None,
        "created_at": datetime.utcnow(),
    }


def new_reply(lead_id: str, **kwargs) -> dict:
    return {
        "_id": generate_id(),
        "lead_id": lead_id,
        "from_email": kwargs.get("from_email", ""),
        "subject": kwargs.get("subject", ""),
        "body": kwargs.get("body", ""),
        "intent": kwargs.get("intent", "unknown"),
        "ai_draft_reply": kwargs.get("ai_draft_reply", ""),
        "is_handled": False,
        "received_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }


def new_suppression(email: str, reason: str = "") -> dict:
    return {
        "_id": generate_id(),
        "email": email,
        "reason": reason,
        "created_at": datetime.utcnow(),
    }


def doc_to_dict(doc: dict) -> dict:
    """Convert a MongoDB document to an API-friendly dict (rename _id -> id)."""
    if doc is None:
        return None
    d = dict(doc)
    d["id"] = d.pop("_id")
    return d
