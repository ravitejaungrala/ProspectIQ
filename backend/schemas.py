from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


# --- Campaign ---
class CampaignCreate(BaseModel):
    product_url: str
    sender_name: str = ""
    sender_title: str = ""
    sender_email: str = ""
    sender_phone: str = ""


class CampaignUpdate(BaseModel):
    product_name: Optional[str] = None
    status: Optional[str] = None
    sender_name: Optional[str] = None
    sender_title: Optional[str] = None
    sender_email: Optional[str] = None
    sender_phone: Optional[str] = None


class CampaignOut(BaseModel):
    id: str
    product_url: str
    product_name: str
    product_summary: str
    ideal_customer_profile: dict
    industries: list
    roles: list
    pain_points: list
    demo_video_url: str = ""
    calendly_url: str = ""
    demo_booking_url: str = ""
    product_phone: str = ""
    contact_emails: list = []
    social_links: dict = {}
    target_domains: list = []
    sender_name: str = ""
    sender_title: str = ""
    sender_email: str = ""
    sender_phone: str = ""
    status: str
    created_at: datetime
    updated_at: datetime
    lead_count: int = 0

    class Config:
        from_attributes = True


class CampaignListOut(BaseModel):
    id: str
    product_url: str
    product_name: str
    status: str
    created_at: datetime
    lead_count: int = 0

    class Config:
        from_attributes = True


# --- Lead ---
class LeadOut(BaseModel):
    id: str
    campaign_id: str
    first_name: str
    last_name: str
    email: str
    company: str
    title: str
    linkedin_url: str
    email_status: str
    profile_score: float
    is_suppressed: bool
    status: str
    drop_reason: str
    last_contacted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadSearchParams(BaseModel):
    domains: list[str] = []
    roles: list[str] = []
    limit: int = 50


# --- Outreach ---
class OutreachStepOut(BaseModel):
    id: str
    lead_id: str
    step_number: int
    step_type: str
    template_type: str = "cold_email"
    role_category: str = "general"
    subject: str
    body: str
    html_body: str = ""
    status: str
    approved: bool = False
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SequenceOut(BaseModel):
    id: str
    campaign_id: str
    name: str
    steps: list
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Reply ---
class ReplyOut(BaseModel):
    id: str
    lead_id: str
    from_email: str
    subject: str
    body: str
    intent: str
    ai_draft_reply: str
    is_handled: bool
    received_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ReplyCreate(BaseModel):
    lead_id: str
    from_email: str
    subject: str
    body: str


# --- Dashboard ---
class DashboardStats(BaseModel):
    total_campaigns: int = 0
    active_campaigns: int = 0
    total_leads: int = 0
    verified_leads: int = 0
    emails_sent: int = 0
    emails_opened: int = 0
    replies_received: int = 0
    interested_replies: int = 0
    demos_booked: int = 0
    open_rate: float = 0.0
    reply_rate: float = 0.0
    interest_rate: float = 0.0


# --- Chat Assistant ---
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = []
    context: dict = {}


class ChatResponse(BaseModel):
    reply: str
    context: dict = {}
    data: dict = {}
