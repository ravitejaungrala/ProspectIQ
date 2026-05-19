"""
Role-based HTML email template engine for ProspectIQ.
Generates branded HTML emails customized by:
  - Email type: cold_email, follow_up, introduction, breakup
  - Recipient role: ceo, manager, hr, marketing, employee, general
  - Company-specific personalization
"""

# ─── Role categories ───────────────────────────────────────────────
ROLE_CATEGORIES = {
    "ceo": ["ceo", "chief executive", "founder", "co-founder", "president", "owner", "managing director"],
    "cto": ["cto", "chief technology", "vp engineering", "vp of engineering", "head of engineering", "director of engineering"],
    "manager": ["manager", "director", "head of", "team lead", "lead", "supervisor", "senior manager"],
    "hr": ["hr", "human resource", "people ops", "people operations", "talent", "recruiter", "chro", "chief people"],
    "marketing": ["marketing", "cmo", "growth", "demand gen", "brand", "content", "digital marketing", "head of marketing"],
    "sales": ["sales", "revenue", "account executive", "business development", "bdr", "sdr", "vp sales", "chief revenue"],
    "employee": ["analyst", "associate", "specialist", "coordinator", "assistant", "engineer", "developer"],
}


def classify_role(title: str) -> str:
    """Classify a job title into a role category."""
    title_lower = title.lower().strip()
    for category, keywords in ROLE_CATEGORIES.items():
        for kw in keywords:
            if kw in title_lower:
                return category
    return "general"


# ─── Subject line variations by role + type ────────────────────────
SUBJECT_LINES = {
    "cold_email": {
        "ceo":       "{first_name}, your {company} ops could save {hours}+ hrs/month",
        "cto":       "{first_name}, how {product_name} integrates with your stack at {company}",
        "manager":   "{first_name}, managing {pain_point} at {company}? Here's data",
        "hr":        "{first_name}, your HR admin hours at {company} — quick audit",
        "marketing": "{first_name}, {product_name} is driving {metric} for teams like {company}",
        "sales":     "{first_name}, pipeline velocity at {company} — a thought",
        "employee":  "{first_name}, a tool your team at {company} will actually use",
        "general":   "{first_name}, one insight about {company} and {pain_point}",
    },
    "follow_up": {
        "ceo":       "Re: {company}'s operational efficiency — new data",
        "cto":       "Re: The technical fit for {company} — 2 min read",
        "manager":   "Re: {pain_point} at {company} — fresh angle",
        "hr":        "Re: {company}'s HR admin time — benchmark comparison",
        "marketing": "Re: {company}'s {pain_point} — a case study",
        "sales":     "Re: Revenue impact for {company} — new numbers",
        "employee":  "Re: Quick follow-up on {product_name} for {company}",
        "general":   "Re: {product_name} for {company} — new value angle",
    },
    "introduction": {
        "ceo":       "{first_name} — {sender_name} here, intro on {product_name}",
        "cto":       "{first_name}, {sender_name} from {product_name} — technical intro",
        "manager":   "{first_name}, quick intro — {product_name} for {company}",
        "hr":        "{first_name}, intro: how {product_name} saves HR teams 70%+ time",
        "marketing": "{first_name}, intro: {product_name} for {company}'s growth",
        "sales":     "{first_name}, {sender_name} intro — revenue acceleration for {company}",
        "employee":  "{first_name}, quick intro to {product_name}",
        "general":   "{first_name}, connecting on {product_name} and {company}",
    },
    "breakup": {
        "ceo":       "Closing the loop, {first_name}",
        "cto":       "Last note, {first_name} — {product_name}",
        "manager":   "Final follow-up, {first_name}",
        "hr":        "Last one, {first_name} — HR efficiency at {company}",
        "marketing": "Closing the loop on {product_name}, {first_name}",
        "sales":     "Wrapping up, {first_name}",
        "employee":  "Last note, {first_name}",
        "general":   "Closing the loop, {first_name}",
    },
}


# ─── AI prompt instructions per role + type ────────────────────────
ROLE_TONE = {
    "ceo":       "Strategic, high-level ROI focus. Talk about market position, competitive edge, cost savings at scale. Respect their time — be extremely concise. No jargon.",
    "cto":       "Technical credibility. Mention integrations, architecture, security, scalability. Data-driven. Respect their engineering mindset.",
    "manager":   "Operational efficiency. Talk about team productivity, process improvement, time savings. Show how it helps them hit their KPIs.",
    "hr":        "People-first language. Focus on compliance, employee experience, admin hour reduction, self-service. Reference HR-specific pain points.",
    "marketing": "Growth metrics. Talk about conversion rates, campaign efficiency, attribution, ROI. Be creative but data-backed.",
    "sales":     "Revenue impact. Pipeline velocity, close rates, deal size. Speak their language — urgency, numbers, results.",
    "employee":  "Practical benefits. How it makes their daily work easier. Simple language, friendly tone. Focus on usability.",
    "general":   "Professional and concise. Focus on the core value proposition and the specific pain point for their company.",
}

TYPE_INSTRUCTIONS = {
    "cold_email": (
        "Write a cold outreach email. Opening line MUST reference something specific about their company "
        "(recent news, growth, team size, a challenge in their industry). Include a personalized hook. "
        "End with a soft CTA (question, not a hard ask). 4-6 short paragraphs max."
    ),
    "follow_up": (
        "Write a follow-up email with a FRESH value angle. Do NOT say 'just checking in' or 'following up on my last email'. "
        "Provide new data, a case study snippet, or a different perspective on their pain point. "
        "Plain text style. 3-4 short paragraphs."
    ),
    "introduction": (
        "Write an introduction email. Introduce yourself and the product briefly. "
        "Explain why you're reaching out specifically to them. Share one concrete result. "
        "Light, warm, professional tone. 3-5 paragraphs."
    ),
    "breakup": (
        "Write a breakup email. Maximum 2-3 sentences. 'Closing the loop' energy. "
        "Acknowledge you don't want to be annoying. Leave the door open. "
        "This format typically has the highest reply rate. Very short."
    ),
}


# ─── Base HTML template (inspired by the NeuzenAI design) ──────────
BASE_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ margin: 0; padding: 0; background: #f5f0eb; font-family: 'Georgia', 'Times New Roman', serif; color: #1a1a1a; }}
  .wrapper {{ max-width: 600px; margin: 0 auto; background: #fffbf7; }}
  .header {{ padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8e0d8; }}
  .header-logo {{ font-size: 18px; font-weight: 700; color: #1a1a1a; letter-spacing: -0.5px; }}
  .header-logo span {{ display: inline-block; width: 28px; height: 28px; background: #e8441e; color: #fff; text-align: center; line-height: 28px; border-radius: 4px; font-size: 14px; margin-right: 8px; vertical-align: middle; }}
  .header-sub {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
  .header-for {{ font-size: 13px; color: #888; }}
  .hero {{ padding: 40px 32px 32px; }}
  .hero-tag {{ font-size: 11px; color: #e8441e; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin-bottom: 12px; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .hero h1 {{ font-size: 32px; line-height: 1.2; font-weight: 700; margin: 0 0 16px; }}
  .hero h1 .accent {{ color: #e8441e; }}
  .hero p {{ font-size: 15px; color: #555; line-height: 1.6; margin: 0; }}
  .personal-note {{ margin: 0 32px 32px; background: #faf6f1; border-left: 3px solid #e8441e; padding: 24px; }}
  .personal-note .label {{ font-size: 11px; color: #e8441e; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin-bottom: 12px; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .personal-note .name-badge {{ display: inline-block; background: #1a1a1a; color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 12px; margin-bottom: 12px; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .personal-note blockquote {{ margin: 0; font-style: italic; font-size: 15px; line-height: 1.7; color: #333; }}
  .personal-note .sig {{ margin-top: 12px; font-size: 13px; color: #888; }}
  .section {{ padding: 32px; border-top: 1px solid #e8e0d8; }}
  .section-label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .section h2 {{ font-size: 22px; font-weight: 700; margin: 0 0 12px; line-height: 1.3; }}
  .section p {{ font-size: 14px; color: #555; line-height: 1.7; }}
  .stats-row {{ display: flex; gap: 0; margin: 20px 0; }}
  .stat-item {{ flex: 1; text-align: center; }}
  .stat-label {{ font-size: 11px; color: #888; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .stat-value {{ font-size: 22px; font-weight: 700; color: #e8441e; margin-top: 4px; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .results-banner {{ background: #1a1a1a; padding: 32px; color: #fff; }}
  .results-banner .label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 16px; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .results-grid {{ display: flex; gap: 16px; }}
  .result-item {{ flex: 1; }}
  .result-item .num {{ font-size: 28px; font-weight: 700; color: #e8441e; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .result-item .desc {{ font-size: 12px; color: #aaa; margin-top: 4px; }}
  .video-section {{ padding: 24px 32px; text-align: center; background: #faf6f1; border-top: 1px solid #e8e0d8; }}
  .video-btn {{ display: inline-block; background: #e8441e; color: #fff; padding: 14px 32px; border-radius: 6px; font-size: 14px; font-weight: 700; text-decoration: none; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .video-label {{ font-size: 12px; color: #888; margin-bottom: 12px; }}
  .cta-section {{ padding: 32px; text-align: center; }}
  .cta-btn {{ display: inline-block; background: #e8441e; color: #fff; padding: 14px 36px; border-radius: 28px; font-size: 15px; font-weight: 700; text-decoration: none; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .cta-sub {{ font-size: 13px; color: #888; margin-top: 12px; }}
  .footer {{ padding: 24px 32px; border-top: 1px solid #e8e0d8; }}
  .footer .name {{ font-size: 15px; font-weight: 700; }}
  .footer .title {{ font-size: 13px; color: #555; }}
  .footer .contact {{ font-size: 13px; color: #888; margin-top: 4px; }}
  .footer .contact a {{ color: #e8441e; text-decoration: none; }}
  .plain-body {{ padding: 32px; font-size: 15px; line-height: 1.8; color: #333; }}
  .plain-body p {{ margin: 0 0 16px; }}
</style>
</head>
<body>
<div class="wrapper">
{content}
</div>
</body>
</html>"""


def _header_html(product_name: str, first_name: str) -> str:
    initial = product_name[0].upper() if product_name else "P"
    return f"""<div class="header">
  <div>
    <div class="header-logo"><span>{initial}</span> {product_name}</div>
  </div>
  <div class="header-for">For &lt;{first_name}&gt;</div>
</div>"""


def _footer_html(sender_name: str, sender_title: str, product_name: str, sender_phone: str, product_url: str) -> str:
    phone_line = f"<br>{sender_phone}" if sender_phone else ""
    return f"""<div class="footer">
  <div class="name">{sender_name or '&lt;sender_name&gt;'}</div>
  <div class="title">{sender_title or 'Growth'} at {product_name}</div>
  <div class="contact">{phone_line}
    {'· ' if sender_phone else ''}<a href="{product_url}">{product_url.replace('https://', '').replace('http://', '')}</a>
  </div>
</div>"""


def _video_section_html(demo_video_url: str) -> str:
    if not demo_video_url:
        return ""
    return f"""<div class="video-section">
  <div class="video-label">SEE IT IN ACTION</div>
  <a href="{demo_video_url}" class="video-btn">▶ Watch 2-min Demo →</a>
</div>"""


def _cta_html(product_url: str, company: str, product_name: str) -> str:
    return f"""<div class="cta-section">
  <a href="{product_url}" class="cta-btn">Book a 20-min demo →</a>
  <div class="cta-sub">No commitment. See exactly how {product_name} maps to {company}.</div>
</div>"""


# ─── Build full branded HTML email ────────────────────────────────

def build_cold_email_html(
    ai_body: str, subject: str,
    first_name: str, company: str, title: str,
    product_name: str, product_summary: str, product_url: str,
    pain_points: list, demo_video_url: str,
    sender_name: str, sender_title: str, sender_phone: str,
    role_category: str,
) -> str:
    """Build branded HTML cold email with hero, personal note, stats, CTA."""
    # Parse AI body into paragraphs
    paragraphs = [p.strip() for p in ai_body.strip().split("\n\n") if p.strip()]
    hook_paragraph = paragraphs[0] if paragraphs else ""
    rest_paragraphs = paragraphs[1:] if len(paragraphs) > 1 else []

    pain = pain_points[0] if pain_points else "operational efficiency"

    hero = f"""<div class="hero">
  <div class="hero-tag">FOR {title.upper()} AT {company.upper()}</div>
  <h1>{subject}</h1>
  <p>{product_summary[:200]}</p>
</div>"""

    personal_note = f"""<div class="personal-note">
  <div class="label">A NOTE FOR {first_name.upper()}</div>
  <div class="name-badge">{first_name}</div>
  <blockquote>"{hook_paragraph}"</blockquote>
  <div class="sig">— {sender_name or '&lt;sender_name&gt;'}</div>
</div>"""

    body_section = ""
    if rest_paragraphs:
        body_html = "".join(f"<p>{p}</p>" for p in rest_paragraphs)
        body_section = f"""<div class="section">
  <section-label>THE VALUE</section-label>
  {body_html}
</div>"""

    content = (
        _header_html(product_name, first_name)
        + hero
        + personal_note
        + body_section
        + _video_section_html(demo_video_url)
        + _cta_html(product_url, company, product_name)
        + _footer_html(sender_name, sender_title, product_name, sender_phone, product_url)
    )
    return BASE_HTML_TEMPLATE.format(content=content)


def build_follow_up_html(
    ai_body: str,
    first_name: str, company: str,
    product_name: str, product_url: str, demo_video_url: str,
    sender_name: str, sender_title: str, sender_phone: str,
) -> str:
    """Build plain-text-style follow-up in branded wrapper."""
    paragraphs = ai_body.strip().split("\n\n")
    body_html = "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

    content = (
        _header_html(product_name, first_name)
        + f'<div class="plain-body">{body_html}</div>'
        + _video_section_html(demo_video_url)
        + _footer_html(sender_name, sender_title, product_name, sender_phone, product_url)
    )
    return BASE_HTML_TEMPLATE.format(content=content)


def build_introduction_html(
    ai_body: str, subject: str,
    first_name: str, company: str, title: str,
    product_name: str, product_summary: str, product_url: str,
    demo_video_url: str,
    sender_name: str, sender_title: str, sender_phone: str,
) -> str:
    """Build intro email with hero + body + video + CTA."""
    paragraphs = ai_body.strip().split("\n\n")
    body_html = "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

    hero = f"""<div class="hero">
  <div class="hero-tag">INTRODUCTION</div>
  <h1>Hi {first_name}, <span class="accent">{sender_name or 'I'}</span> here.</h1>
  <p>{product_summary[:200]}</p>
</div>"""

    content = (
        _header_html(product_name, first_name)
        + hero
        + f'<div class="plain-body">{body_html}</div>'
        + _video_section_html(demo_video_url)
        + _cta_html(product_url, company, product_name)
        + _footer_html(sender_name, sender_title, product_name, sender_phone, product_url)
    )
    return BASE_HTML_TEMPLATE.format(content=content)


def build_breakup_html(
    ai_body: str,
    first_name: str, company: str,
    product_name: str, product_url: str,
    sender_name: str, sender_title: str, sender_phone: str,
) -> str:
    """Build short breakup email. Minimal, no video, no heavy CTA."""
    paragraphs = ai_body.strip().split("\n\n")
    body_html = "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

    content = (
        _header_html(product_name, first_name)
        + f'<div class="plain-body">{body_html}</div>'
        + _footer_html(sender_name, sender_title, product_name, sender_phone, product_url)
    )
    return BASE_HTML_TEMPLATE.format(content=content)


# ─── Main entry point ─────────────────────────────────────────────

def build_email_html(
    template_type: str, ai_body: str, subject: str,
    first_name: str, company: str, title: str,
    product_name: str, product_summary: str, product_url: str,
    pain_points: list, demo_video_url: str,
    sender_name: str, sender_title: str, sender_phone: str,
    role_category: str,
) -> str:
    """Route to the correct HTML builder by template type."""
    if template_type == "cold_email":
        return build_cold_email_html(
            ai_body, subject, first_name, company, title,
            product_name, product_summary, product_url,
            pain_points, demo_video_url,
            sender_name, sender_title, sender_phone, role_category,
        )
    elif template_type == "follow_up":
        return build_follow_up_html(
            ai_body, first_name, company,
            product_name, product_url, demo_video_url,
            sender_name, sender_title, sender_phone,
        )
    elif template_type == "introduction":
        return build_introduction_html(
            ai_body, subject, first_name, company, title,
            product_name, product_summary, product_url,
            demo_video_url,
            sender_name, sender_title, sender_phone,
        )
    elif template_type == "breakup":
        return build_breakup_html(
            ai_body, first_name, company,
            product_name, product_url,
            sender_name, sender_title, sender_phone,
        )
    else:
        # Default: plain text in branded wrapper
        return build_follow_up_html(
            ai_body, first_name, company,
            product_name, product_url, demo_video_url,
            sender_name, sender_title, sender_phone,
        )


def get_subject_line(
    template_type: str, role_category: str,
    first_name: str, company: str, product_name: str,
    sender_name: str, pain_points: list,
) -> str:
    """Get the subject line template for a given type + role, with variables filled."""
    pain = pain_points[0] if pain_points else "operational efficiency"
    subjects = SUBJECT_LINES.get(template_type, SUBJECT_LINES["cold_email"])
    template = subjects.get(role_category, subjects["general"])
    return template.format(
        first_name=first_name,
        company=company,
        product_name=product_name,
        sender_name=sender_name or "Our team",
        pain_point=pain,
        hours="100",
        metric="3x ROI",
    )
