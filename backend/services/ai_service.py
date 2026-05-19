import google.generativeai as genai
import json
from config import get_settings

settings = get_settings()

if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)


def _get_model():
    return genai.GenerativeModel(settings.gemini_model)


async def extract_product_info(website_content: str) -> dict:
    """Extract product summary, ICP, industries, roles, and pain points from website content."""
    model = _get_model()
    prompt = f"""Analyze the following website content and extract structured information about the product/service.

Return a JSON object with these fields:
- "product_name": The name of the product or service
- "product_summary": A 2-3 sentence summary of what the product does
- "ideal_customer_profile": An object describing the ideal customer with fields: company_size, revenue_range, tech_stack, geography
- "industries": An array of 3-5 target industries (e.g., ["SaaS", "FinTech", "Healthcare"])
- "roles": An array of 3-5 target job roles/titles (e.g., ["VP of Sales", "CTO", "Head of Marketing"])
- "pain_points": An array of 3-5 pain points this product solves
- "target_domains": An array of 10-15 real company website domains that would be ideal customers for this product. These should be real companies that exist, in the right industries and company size. Use ONLY the root domain (e.g., "stripe.com", "hubspot.com", "shopify.com"). Focus on companies that would genuinely benefit from this product based on the ICP.
- "demo_video_url": URL of any product demo or explainer video found on the site (YouTube, Vimeo, Loom etc.), or empty string if none found
- "phone": Any contact phone number found on the site, or empty string

Website Content:
{website_content[:8000]}

Return ONLY valid JSON, no markdown formatting or code blocks."""

    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


async def score_lead_fit(lead_info: dict, icp: dict) -> float:
    """Score how well a lead matches the ideal customer profile. Returns 0-100."""
    model = _get_model()
    prompt = f"""Score how well this lead matches the ideal customer profile on a scale of 0-100.

Lead:
- Name: {lead_info.get('first_name', '')} {lead_info.get('last_name', '')}
- Title: {lead_info.get('title', '')}
- Company: {lead_info.get('company', '')}

Ideal Customer Profile:
{json.dumps(icp, indent=2)}

Target Industries: {lead_info.get('industries', [])}
Target Roles: {lead_info.get('roles', [])}

Return ONLY a number between 0 and 100, nothing else."""

    response = model.generate_content(prompt)
    try:
        return float(response.text.strip())
    except ValueError:
        return 50.0


from services.email_templates import (
    classify_role, ROLE_TONE, TYPE_INSTRUCTIONS,
    build_email_html, get_subject_line,
)


async def personalize_email(lead_info: dict, product_info: dict, step_type: str, campaign: dict = None) -> dict:
    """Generate a role-based personalized email with HTML body.
    
    Returns dict with: subject, body (plain text), html_body, role_category, template_type
    """
    model = _get_model()

    # Map old step_type names to template types
    type_map = {
        "cold_email": "cold_email",
        "fresh_angle": "follow_up",
        "video": "follow_up",
        "breakup": "breakup",
        "follow_up": "follow_up",
        "introduction": "introduction",
    }
    template_type = type_map.get(step_type, "cold_email")

    # Classify the lead's role
    title = lead_info.get("title", "")
    role_category = classify_role(title)

    first_name = lead_info.get("first_name", "there")
    company = lead_info.get("company", "your company")
    product_name = product_info.get("product_name", "Our Product")
    product_summary = product_info.get("product_summary", "")
    pain_points = product_info.get("pain_points", [])

    # Campaign-level sender info
    sender_name = (campaign or {}).get("sender_name", "")
    sender_title = (campaign or {}).get("sender_title", "")
    sender_phone = (campaign or {}).get("sender_phone", "")
    demo_video_url = (campaign or {}).get("demo_video_url", "")
    product_url = (campaign or {}).get("product_url", "")
    product_phone = (campaign or {}).get("product_phone", "")

    # Role tone + type instructions for AI
    role_tone = ROLE_TONE.get(role_category, ROLE_TONE["general"])
    type_instr = TYPE_INSTRUCTIONS.get(template_type, TYPE_INSTRUCTIONS["cold_email"])

    # Get subject line
    subject = get_subject_line(
        template_type, role_category,
        first_name, company, product_name, sender_name, pain_points,
    )

    prompt = f"""Generate a sales outreach email body (plain text).

Product: {product_name}
Product Summary: {product_summary}
Pain points product solves: {', '.join(pain_points[:3])}
Product URL: {product_url}
{f'Demo video: {demo_video_url}' if demo_video_url else ''}
{f'Sender: {sender_name}, {sender_title}' if sender_name else ''}
{f'Phone: {sender_phone or product_phone}' if (sender_phone or product_phone) else ''}

Lead:
- Name: {first_name} {lead_info.get('last_name', '')}
- Title: {title}
- Company: {company}
- Role category: {role_category}

ROLE TONE: {role_tone}

EMAIL TYPE: {template_type}
{type_instr}

CRITICAL RULES:
- Write the email body only. No subject line. No greeting like "Subject:".
- Start directly with the personalized opening.
- Include the product name naturally.
- If a demo video URL exists, mention watching a quick demo.
- If phone number exists, reference "feel free to call".
- Use double newlines between paragraphs.
- Appropriate tone for a {role_category.upper()} recipient.
- End with a soft call-to-action.

Return ONLY the plain text email body, nothing else."""

    response = model.generate_content(prompt)
    body_text = response.text.strip()

    # Build HTML version
    html_body = build_email_html(
        template_type=template_type,
        ai_body=body_text,
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
        sender_phone=sender_phone or product_phone,
        role_category=role_category,
    )

    return {
        "subject": subject,
        "body": body_text,
        "html_body": html_body,
        "role_category": role_category,
        "template_type": template_type,
    }


async def generate_linkedin_message(lead_info: dict, product_info: dict) -> str:
    """Generate a LinkedIn message. 4-5 lines, no emojis, no buzzwords."""
    model = _get_model()
    prompt = f"""Write a LinkedIn connection/outreach message.

Product: {product_info.get('product_name', 'Our Product')}
Product Summary: {product_info.get('product_summary', '')}

Lead:
- Name: {lead_info.get('first_name', '')} {lead_info.get('last_name', '')}
- Title: {lead_info.get('title', '')}
- Company: {lead_info.get('company', '')}

Rules:
- 4-5 lines maximum
- No emojis
- No buzzwords
- Professional and direct tone

Return ONLY the message text, nothing else."""

    response = model.generate_content(prompt)
    return response.text.strip()


async def classify_reply_intent(reply_body: str) -> str:
    """Classify the intent of a reply. Returns: interested, question, not_interested, out_of_office, demo, unsubscribe."""
    model = _get_model()
    prompt = f"""Classify the intent of this email reply into one of these categories:
- interested: The person wants to learn more or continue the conversation
- question: They have a specific question about the product
- demo: They want to book a demo or meeting
- not_interested: They are not interested
- out_of_office: Auto-reply or out of office
- unsubscribe: They want to be removed from the list

Reply:
{reply_body[:2000]}

Return ONLY one of: interested, question, not_interested, out_of_office, demo, unsubscribe"""

    response = model.generate_content(prompt)
    intent = response.text.strip().lower()
    valid_intents = ["interested", "question", "not_interested", "out_of_office", "demo", "unsubscribe"]
    return intent if intent in valid_intents else "question"


async def draft_reply(original_reply: str, intent: str, product_info: dict, knowledge_base: str = "") -> str:
    """Draft an AI reply based on the classified intent."""
    model = _get_model()
    prompt = f"""Draft a reply to this email. The sender's intent is: {intent}

Original email:
{original_reply[:2000]}

Product Info:
{json.dumps(product_info, indent=2)}

{f'Knowledge Base Context: {knowledge_base[:2000]}' if knowledge_base else ''}

Instructions based on intent:
- interested: Thank them, suggest next steps, propose a meeting time
- question: Answer their question using product info and knowledge base
- demo: Confirm interest, provide a booking link placeholder [BOOKING_LINK]
- not_interested: Thank them politely, leave the door open
- out_of_office: Note to follow up later
- unsubscribe: Confirm removal, apologize for the inconvenience

Keep the reply professional, concise, and helpful. Return ONLY the reply text."""

    response = model.generate_content(prompt)
    return response.text.strip()
