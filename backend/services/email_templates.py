"""
ProspectIQ — 6 premium HTML email templates.
Random template selection per email type for A/B variation.
Email-safe HTML (no Canvas, no JS, no SVG).
"""

import random

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


# ═══════════════════════════════════════════════════════════════════
#  SHARED CSS (email-safe)
# ═══════════════════════════════════════════════════════════════════

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
.shell{background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8e2f5;max-width:640px;margin:0 auto}
.eh{display:flex;align-items:center;justify-content:space-between;padding:16px 28px;border-bottom:1px solid #f0eaf9}
.elogo{display:flex;align-items:center;gap:9px}
.emark{width:28px;height:28px;background:#7c3aed;border-radius:7px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:800}
.ename{font-size:14px;font-weight:700;color:#1a1a2e;letter-spacing:-.3px}
.esub{font-size:9px;color:#b0a3d4;text-transform:uppercase;letter-spacing:1.2px}
.efor{font-size:11px;color:#b0a3d4}.efor b{color:#7c3aed}
.hero{padding:32px 28px 22px}
.eyebrow{font-size:10px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:#ec4899;margin-bottom:10px}
.hero h1{font-size:26px;line-height:1.22;font-weight:700;color:#1a1a2e;margin-bottom:10px;font-family:Georgia,serif}
.hero h1 .vp{color:#7c3aed}.hero h1 .vb{color:#2563eb}.hero h1 .vpk{color:#ec4899}
.hero p{font-size:13px;color:#6b7280;line-height:1.68}
.pnote{margin:0 28px 20px;background:#faf7ff;border-left:3px solid #7c3aed;border-radius:0 8px 8px 0;padding:18px 20px}
.pnote-lbl{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#7c3aed;margin-bottom:8px}
.pnote-badge{display:inline-block;background:#1a1a2e;color:#fff;padding:2px 9px;border-radius:4px;font-size:10px;margin-bottom:8px}
.pnote blockquote{font-style:italic;font-size:13px;line-height:1.7;color:#374151;margin:0}
.pnote .sig{margin-top:8px;font-size:11px;color:#b0a3d4}
.sec{padding:22px 28px;border-top:1px solid #f0eaf9}
.sec-lbl{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#b0a3d4;margin-bottom:6px}
.sec h2{font-size:17px;font-weight:700;color:#1a1a2e;margin-bottom:8px;font-family:Georgia,serif}
.sec p{font-size:13px;color:#4b5563;line-height:1.7;margin-bottom:8px}
.stats{display:flex;border:1px solid #ede9f9;border-radius:10px;overflow:hidden;margin:0 28px 18px}
.stat{flex:1;padding:14px 8px;text-align:center;background:#faf7ff;border-right:1px solid #ede9f9}
.stat:last-child{border-right:none}
.sv{font-size:20px;font-weight:700}.sl{font-size:9px;color:#9ca3af;text-transform:uppercase;letter-spacing:.8px;margin-top:2px}
.cp{color:#7c3aed}.cb{color:#2563eb}.cpk{color:#ec4899}
.roi{background:#1a1a2e;padding:22px 28px;color:#fff}
.roi-lbl{font-size:9px;color:#6b7280;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px}
.roi-g{display:flex}
.ri{flex:1;text-align:center;border-right:1px solid rgba(255,255,255,.12)}
.ri:last-child{border-right:none}
.rn{font-size:24px;font-weight:800}.rd{font-size:10px;color:#9ca3af;margin-top:2px}
.prog-wrap{padding:16px 28px 8px}
.pr{margin-bottom:12px}
.pr-row{display:flex;justify-content:space-between;margin-bottom:4px}
.pr-name{font-size:12px;color:#374151;font-weight:600}
.pr-val{font-size:12px;color:#7c3aed;font-weight:700}
.pr-track{height:7px;background:#ede9f9;border-radius:4px;overflow:hidden}
.pr-bar{height:100%;border-radius:4px}
.flow{padding:18px 28px;background:#faf7ff;border-top:1px solid #f0eaf9}
.flow-lbl{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#b0a3d4;margin-bottom:14px}
.flow-row{display:flex;align-items:flex-start;gap:0}
.fs{flex:1;text-align:center;position:relative}
.fs:not(:last-child)::after{content:'→';position:absolute;right:-6px;top:13px;font-size:14px;color:#c4b5fd}
.fi{width:36px;height:36px;border-radius:50%;margin:0 auto 6px;display:flex;align-items:center;justify-content:center;font-size:15px}
.ft{font-size:11px;font-weight:700;color:#1a1a2e}
.fd{font-size:10px;color:#9ca3af;margin-top:2px;line-height:1.35}
.steps{padding:18px 28px 4px}
.step{display:flex;gap:14px;align-items:flex-start;margin-bottom:16px}
.snum{width:26px;height:26px;border-radius:50%;background:#7c3aed;color:#fff;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.stitle{font-size:12px;font-weight:700;color:#1a1a2e;margin-bottom:2px}
.sdesc{font-size:11px;color:#6b7280;line-height:1.55}
.ctable{width:100%;border-collapse:collapse;font-size:12px}
.ctable th{background:#1a1a2e;color:#fff;padding:9px 10px;text-align:left;font-weight:600;font-size:10px;letter-spacing:.5px}
.ctable td{padding:9px 10px;border-bottom:1px solid #f0eaf9;color:#374151}
.ctable tr:nth-child(even) td{background:#faf7ff}
.ck{color:#7c3aed;font-size:13px}.cx{color:#f87171;font-size:13px}
.missing{list-style:none;padding:0;margin:0}
.missing li{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-bottom:1px solid #f0eaf9;font-size:12px;color:#374151}
.missing li:last-child{border-bottom:none}
.mdot{width:7px;height:7px;border-radius:50%;flex-shrink:0;margin-top:4px}
.evid{padding:16px 28px;text-align:center;background:#faf7ff;border-top:1px solid #f0eaf9}
.vl{font-size:9px;color:#b0a3d4;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px}
.vid-btn{display:inline-block;background:#2563eb;color:#fff;padding:10px 22px;border-radius:6px;font-size:12px;font-weight:700;text-decoration:none}
.cta{padding:22px 28px;text-align:center}
.cta-btn{display:inline-block;background:#7c3aed;color:#fff;padding:12px 30px;border-radius:28px;font-size:13px;font-weight:700;text-decoration:none}
.cta-sub{font-size:11px;color:#b0a3d4;margin-top:8px}
.ef{padding:16px 28px;border-top:1px solid #e8e2f5}
.efn{font-size:13px;font-weight:700;color:#1a1a2e}
.eft{font-size:11px;color:#4b5563}
.efc{font-size:11px;color:#b0a3d4;margin-top:2px}
.efc a{color:#7c3aed;text-decoration:none}
.plain{padding:22px 28px;font-size:13px;line-height:1.8;color:#374151}
.plain p{margin-bottom:12px}
.lbar{padding:16px 28px;border-top:1px solid #f0eaf9}
.lbar-lbl{font-size:9px;color:#b0a3d4;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px}
.lbar-row{display:flex;gap:10px;flex-wrap:wrap}
.lpill{padding:5px 12px;border-radius:20px;font-size:10px;font-weight:700;letter-spacing:.4px}
.bar-chart{padding:4px 28px 16px}
.bar-row{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.bar-label{font-size:10px;color:#374151;width:80px;text-align:right;font-weight:600}
.bar-track{flex:1;height:16px;background:#ede9f9;border-radius:4px;overflow:hidden;position:relative}
.bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;justify-content:flex-end;padding-right:6px;font-size:9px;font-weight:700;color:#fff}
.donut-row{display:flex;margin:0 28px 16px;border-radius:10px;overflow:hidden}
"""


# ─── Placeholder renderer ────────────────────────────────────────

def _r(tpl: str, **kw) -> str:
    """Replace [[key]] placeholders in template."""
    for k, v in kw.items():
        tpl = tpl.replace(f"[[{k}]]", str(v) if v else "")
    return tpl


def _wrap(body_html: str) -> str:
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<style>{_CSS}</style></head>'
        '<body style="margin:0;padding:0;background:#f0edf8;font-family:\'Helvetica Neue\',Arial,sans-serif;color:#1a1a2e">'
        '<div style="max-width:640px;margin:0 auto;padding:24px 16px">'
        f'{body_html}'
        '</div></body></html>'
    )


def _header(product_name: str, first_name: str) -> str:
    ini = product_name[0].upper() if product_name else "P"
    return (
        '<div class="eh">'
        '<div class="elogo">'
        f'<div class="emark">{ini}</div>'
        f'<div><div class="ename">{product_name}</div><div class="esub">AI-Powered Outreach</div></div>'
        '</div>'
        f'<div class="efor">For <b>{first_name}</b></div>'
        '</div>'
    )


def _footer(sender_name: str, sender_title: str, product_name: str, phone: str, url: str) -> str:
    url_clean = url.replace("https://", "").replace("http://", "").rstrip("/")
    phone_bit = f'{phone} · ' if phone else ''
    return (
        '<div class="ef">'
        f'<div class="efn">{sender_name or "Our team"}</div>'
        f'<div class="eft">{sender_title or "Growth"} at {product_name}</div>'
        f'<div class="efc">{phone_bit}<a href="{url}">{url_clean}</a></div>'
        '</div>'
    )


def _video(demo_url: str) -> str:
    if not demo_url:
        return ""
    return (
        '<div class="evid"><div class="vl">See It in Action</div>'
        f'<a href="{demo_url}" class="vid-btn" style="color:#fff;text-decoration:none">▶ Watch 2-min Demo →</a></div>'
    )


def _cta(url: str, company: str, product_name: str, label: str = "Book a 20-min strategy call →") -> str:
    return (
        '<div class="cta">'
        f'<a href="{url}" class="cta-btn" style="color:#fff;text-decoration:none">{label}</a>'
        f'<div class="cta-sub">No commitment. See exactly how {product_name} maps to {company}.</div>'
        '</div>'
    )


# ═══════════════════════════════════════════════════════════════════
#  TEMPLATE 1 — COLD EMAIL (Signal-Led)
# ═══════════════════════════════════════════════════════════════════

def _tpl_cold_signal(ai_body, subject, first_name, company, title,
                     product_name, product_summary, product_url,
                     pain_points, demo_video_url,
                     sender_name, sender_title, sender_phone, role_cat):
    paras = [p.strip() for p in ai_body.strip().split("\n\n") if p.strip()]
    hook = paras[0] if paras else ""
    rest = paras[1:] if len(paras) > 1 else []
    rest_html = "".join(f"<p>{p}</p>" for p in rest)
    pain = pain_points[0] if pain_points else "operational efficiency"

    return _wrap(
        '<div class="shell">'
        + _header(product_name, first_name)
        # Hero
        + '<div class="hero">'
        + f'<div class="eyebrow">For {title} at {company}</div>'
        + f'<h1>{subject}</h1>'
        + f'<p>{product_summary[:200]}</p>'
        + '</div>'
        # Personal note with AI hook
        + '<div class="pnote">'
        + f'<div class="pnote-lbl">A note for {first_name}</div>'
        + f'<div class="pnote-badge">{first_name} · {title}</div>'
        + f'<blockquote>"{hook}"</blockquote>'
        + f'<div class="sig">— {sender_name or "Our team"}, {sender_title or "Growth"}</div>'
        + '</div>'
        # Problem section with AI rest
        + '<div class="sec">'
        + '<div class="sec-lbl">01 · The Problem</div>'
        + f'<h2>Why {company} needs to act on {pain}</h2>'
        + rest_html
        + '</div>'
        # Stats
        + '<div class="stats">'
        + '<div class="stat"><div class="sv cp">90%</div><div class="sl">Time saved</div></div>'
        + '<div class="stat"><div class="sv cpk">68%</div><div class="sl">Less manual work</div></div>'
        + '<div class="stat"><div class="sv cb">2.8×</div><div class="sl">More output</div></div>'
        + '<div class="stat"><div class="sv cp">14 days</div><div class="sl">To first result</div></div>'
        + '</div>'
        # How it works flow
        + '<div class="flow">'
        + f'<div class="flow-lbl">How {product_name} Works</div>'
        + '<div class="flow-row">'
        + '<div class="fs"><div class="fi" style="background:#ede9fe">🔍</div><div class="ft">Analyze</div><div class="fd">Understand your needs</div></div>'
        + '<div class="fs"><div class="fi" style="background:#fce7f3">🧠</div><div class="ft">Automate</div><div class="fd">AI-powered execution</div></div>'
        + '<div class="fs"><div class="fi" style="background:#dbeafe">⚡</div><div class="ft">Deliver</div><div class="fd">Results in days</div></div>'
        + '<div class="fs"><div class="fi" style="background:#ede9fe">📈</div><div class="ft">Scale</div><div class="fd">Continuous growth</div></div>'
        + '</div></div>'
        # ROI
        + '<div class="roi">'
        + f'<div class="roi-lbl">{product_name} ROI · At a Glance</div>'
        + '<div class="roi-g">'
        + '<div class="ri"><div class="rn" style="color:#c4b5fd">3.2×</div><div class="rd">Avg ROI</div></div>'
        + '<div class="ri"><div class="rn" style="color:#f9a8d4">92%</div><div class="rd">Satisfaction</div></div>'
        + '<div class="ri"><div class="rn" style="color:#93c5fd">14 days</div><div class="rd">To first result</div></div>'
        + '</div></div>'
        + _video(demo_video_url)
        + _cta(product_url, company, product_name)
        + _footer(sender_name, sender_title, product_name, sender_phone, product_url)
        + '</div>'
    )


# ═══════════════════════════════════════════════════════════════════
#  TEMPLATE 2 — FOLLOW-UP (Benchmark Data)
# ═══════════════════════════════════════════════════════════════════

def _tpl_followup_benchmark(ai_body, subject, first_name, company, title,
                            product_name, product_summary, product_url,
                            pain_points, demo_video_url,
                            sender_name, sender_title, sender_phone, role_cat):
    paras = [p.strip() for p in ai_body.strip().split("\n\n") if p.strip()]
    body_html = "".join(f"<p>{p}</p>" for p in paras)
    pain = pain_points[0] if pain_points else "operational efficiency"

    return _wrap(
        '<div class="shell">'
        + _header(product_name, first_name)
        # Hero
        + '<div class="hero" style="padding-bottom:14px">'
        + f'<div class="eyebrow">Re: {pain} at {company} — new data</div>'
        + f'<h1>Instead of following up,<br>I brought <span class="vp">benchmark data</span>.</h1>'
        + f'<p>Among companies at {company}\'s stage that adopted {product_name}, here\'s what 90 days looks like.</p>'
        + '</div>'
        # Before vs After section
        + '<div class="sec" style="padding-bottom:4px">'
        + '<div class="sec-lbl">Before vs After · 90-Day Cohort</div>'
        + f'<h2>What teams like {company} are achieving</h2>'
        + '</div>'
        + '<div class="prog-wrap">'
        + '<div style="display:flex;gap:0;margin-bottom:14px">'
        + '<div style="flex:1;text-align:center;padding:8px;background:#faf7ff;border-radius:8px 0 0 8px;border:1px solid #e8e2f5;font-size:10px;font-weight:700;color:#7c3aed">BEFORE</div>'
        + f'<div style="flex:1;text-align:center;padding:8px;background:#7c3aed;border-radius:0 8px 8px 0;font-size:10px;font-weight:700;color:#fff">AFTER {product_name}</div>'
        + '</div>'
        + '<div class="pr"><div class="pr-row"><span class="pr-name">Efficiency Rate</span><span class="pr-val">12% → 31%</span></div><div class="pr-track"><div class="pr-bar" style="width:31%;background:#7c3aed"></div></div></div>'
        + '<div class="pr"><div class="pr-row"><span class="pr-name">Time Saved / Week</span><span class="pr-val">2h → 12h</span></div><div class="pr-track"><div class="pr-bar" style="width:66%;background:#2563eb"></div></div></div>'
        + '<div class="pr"><div class="pr-row"><span class="pr-name">Manual Tasks Remaining</span><span class="pr-val">74% → 18%</span></div><div class="pr-track"><div class="pr-bar" style="width:18%;background:#ec4899"></div></div></div>'
        + '<div class="pr"><div class="pr-row"><span class="pr-name">Team Adoption</span><span class="pr-val">41% → 79%</span></div><div class="pr-track"><div class="pr-bar" style="width:79%;background:#7c3aed"></div></div></div>'
        + '</div>'
        # ROI
        + '<div class="roi">'
        + f'<div class="roi-lbl">Quick ROI Estimate for {company}</div>'
        + '<div class="roi-g">'
        + '<div class="ri"><div class="rn" style="color:#c4b5fd">3.2×</div><div class="rd">Avg ROI</div></div>'
        + '<div class="ri"><div class="rn" style="color:#f9a8d4">18×</div><div class="rd">ROI at your scale</div></div>'
        + '<div class="ri"><div class="rn" style="color:#93c5fd">43 days</div><div class="rd">Payback period</div></div>'
        + '</div></div>'
        # AI body
        + f'<div class="plain">{body_html}</div>'
        + _video(demo_video_url)
        + _footer(sender_name, sender_title, product_name, sender_phone, product_url)
        + '</div>'
    )


# ═══════════════════════════════════════════════════════════════════
#  TEMPLATE 3 — INTRODUCTION (End-to-End Flow)
# ═══════════════════════════════════════════════════════════════════

def _tpl_intro_flow(ai_body, subject, first_name, company, title,
                    product_name, product_summary, product_url,
                    pain_points, demo_video_url,
                    sender_name, sender_title, sender_phone, role_cat):
    paras = [p.strip() for p in ai_body.strip().split("\n\n") if p.strip()]
    body_html = "".join(f"<p>{p}</p>" for p in paras)

    return _wrap(
        '<div class="shell">'
        + _header(product_name, first_name)
        # Hero
        + '<div class="hero">'
        + '<div class="eyebrow">Introduction</div>'
        + f'<h1>Hi {first_name},<br><span class="vb">{sender_name or "I"}</span> here.</h1>'
        + f'<p>I\'m reaching out because {company} is at exactly the stage where {product_name} has the most impact — and I wanted to introduce myself properly before anything else.</p>'
        + '</div>'
        # How it works flow
        + '<div class="flow">'
        + f'<div class="flow-lbl">End-to-End · How {product_name} Works</div>'
        + '<div class="flow-row">'
        + '<div class="fs"><div class="fi" style="background:#ede9fe">🔍</div><div class="ft">Discover</div><div class="fd">Map your needs & stack</div></div>'
        + '<div class="fs"><div class="fi" style="background:#fce7f3">🧠</div><div class="ft">Configure</div><div class="fd">AI adapts to your workflow</div></div>'
        + '<div class="fs"><div class="fi" style="background:#dbeafe">⚡</div><div class="ft">Deploy</div><div class="fd">Live in days, not months</div></div>'
        + '<div class="fs"><div class="fi" style="background:#ede9fe">📈</div><div class="ft">Results</div><div class="fd">Measurable ROI fast</div></div>'
        + '</div></div>'
        # Onboarding steps
        + '<div class="sec" style="padding-bottom:4px">'
        + '<div class="sec-lbl">Onboarding · Step by Step</div>'
        + '<h2>From intro call to first win</h2>'
        + '</div>'
        + '<div class="steps">'
        + '<div class="step"><div class="snum">1</div><div><div class="stitle">Day 1 — Strategy Call (20 min)</div><div class="sdesc">Map your goals and current workflow. No prep needed on your side.</div></div></div>'
        + '<div class="step"><div class="snum">2</div><div><div class="stitle">Day 2–3 — Setup & Integration</div><div class="sdesc">Connect your existing tools. Your team works the same way — we augment it.</div></div></div>'
        + f'<div class="step"><div class="snum">3</div><div><div class="stitle">Day 4–7 — {product_name} Learns</div><div class="sdesc">AI trains on your specific data and use case. Personalized, not generic.</div></div></div>'
        + '<div class="step" style="margin-bottom:0"><div class="snum">4</div><div><div class="stitle">Day 8–14 — First Results</div><div class="sdesc">See measurable impact in the first two weeks. Dedicated support throughout.</div></div></div>'
        + '</div>'
        # ROI
        + '<div class="roi">'
        + '<div class="roi-lbl">Introduction ROI Snapshot</div>'
        + '<div class="roi-g">'
        + '<div class="ri"><div class="rn" style="color:#c4b5fd">3.2×</div><div class="rd">Avg ROI</div></div>'
        + '<div class="ri"><div class="rn" style="color:#f9a8d4">92%</div><div class="rd">Satisfaction</div></div>'
        + '<div class="ri"><div class="rn" style="color:#93c5fd">14 days</div><div class="rd">To first result</div></div>'
        + '</div></div>'
        # AI body
        + f'<div class="plain">{body_html}</div>'
        + _video(demo_video_url)
        + _cta(product_url, company, product_name, "Book a 20-min intro call →")
        + _footer(sender_name, sender_title, product_name, sender_phone, product_url)
        + '</div>'
    )


# ═══════════════════════════════════════════════════════════════════
#  TEMPLATE 4 — BREAKUP (Last Note + What You Missed)
# ═══════════════════════════════════════════════════════════════════

def _tpl_breakup_honest(ai_body, subject, first_name, company, title,
                        product_name, product_summary, product_url,
                        pain_points, demo_video_url,
                        sender_name, sender_title, sender_phone, role_cat):
    paras = [p.strip() for p in ai_body.strip().split("\n\n") if p.strip()]
    body_html = "".join(f"<p>{p}</p>" for p in paras)
    pp = pain_points[:4] if pain_points else ["Streamlined workflow", "Time savings", "Better insights", "Dedicated support"]
    colors = ["#7c3aed", "#ec4899", "#2563eb", "#7c3aed"]

    bullets = ""
    for i, point in enumerate(pp):
        c = colors[i % len(colors)]
        bullets += f'<li><div class="mdot" style="background:{c}"></div><div><strong>{point}</strong></div></li>'

    return _wrap(
        '<div class="shell">'
        + _header(product_name, first_name)
        # Hero
        + '<div class="hero" style="padding-bottom:14px">'
        + '<div class="eyebrow">Closing the Loop</div>'
        + f'<h1>Last note, {first_name} —<br><span class="vp">and one honest question.</span></h1>'
        + '</div>'
        # AI body
        + f'<div class="plain">{body_html}</div>'
        # What you missed
        + '<div class="sec" style="padding-top:14px">'
        + '<div class="sec-lbl">What We Didn\'t Get to Show You</div>'
        + '<h2>A summary of what\'s on the table</h2>'
        + f'<ul class="missing">{bullets}</ul>'
        + '</div>'
        # ROI
        + '<div class="roi">'
        + '<div class="roi-lbl">What Teams Achieve in 90 Days</div>'
        + '<div class="roi-g">'
        + '<div class="ri"><div class="rn" style="color:#c4b5fd">+158%</div><div class="rd">Efficiency gained</div></div>'
        + '<div class="ri"><div class="rn" style="color:#f9a8d4">+38%</div><div class="rd">Adoption</div></div>'
        + '<div class="ri"><div class="rn" style="color:#93c5fd">18×</div><div class="rd">ROI</div></div>'
        + '</div></div>'
        # Donut replacement — two-tone bar
        + '<div class="donut-row">'
        + f'<div style="flex:58;text-align:center;padding:14px;background:#7c3aed;color:#fff"><div style="font-size:20px;font-weight:700">58%</div><div style="font-size:9px;opacity:.8">Use {product_name}</div></div>'
        + '<div style="flex:42;text-align:center;padding:14px;background:#faf7ff;border:1px solid #e8e2f5"><div style="font-size:20px;font-weight:700;color:#7c3aed">42%</div><div style="font-size:9px;color:#9ca3af">Don\'t — yet</div></div>'
        + '</div>'
        + '<div class="plain" style="padding-top:8px"><p style="font-size:11px;color:#b0a3d4">Either way — genuinely wishing you a strong quarter. You know where to find me. 👋</p></div>'
        + _footer(sender_name, sender_title, product_name, sender_phone, product_url)
        + '</div>'
    )


# ═══════════════════════════════════════════════════════════════════
#  TEMPLATE 5 — CEO / EXECUTIVE (Board-Level ROI)
# ═══════════════════════════════════════════════════════════════════

def _tpl_ceo_executive(ai_body, subject, first_name, company, title,
                       product_name, product_summary, product_url,
                       pain_points, demo_video_url,
                       sender_name, sender_title, sender_phone, role_cat):
    paras = [p.strip() for p in ai_body.strip().split("\n\n") if p.strip()]
    body_html = "".join(f"<p>{p}</p>" for p in paras)
    pain = pain_points[0] if pain_points else "operational efficiency"

    return _wrap(
        '<div class="shell">'
        + _header(product_name, first_name)
        # Hero
        + '<div class="hero">'
        + f'<div class="eyebrow">For the {title} at {company}</div>'
        + f'<h1>{subject}</h1>'
        + f'<p>{product_summary[:200]}</p>'
        + '</div>'
        # Board-level stats
        + '<div class="sec">'
        + '<div class="sec-lbl">Executive-Level Impact</div>'
        + f'<h2>Three numbers that matter for {company}</h2>'
        + '</div>'
        + '<div class="stats">'
        + '<div class="stat"><div class="sv cp">70%</div><div class="sl">Less manual work</div></div>'
        + '<div class="stat"><div class="sv cpk">+38%</div><div class="sl">Team productivity</div></div>'
        + '<div class="stat"><div class="sv cb">18×</div><div class="sl">ROI at your scale</div></div>'
        + '</div>'
        # Bar chart — efficiency by area
        + '<div class="sec" style="padding-bottom:6px">'
        + '<div class="sec-lbl">Efficiency Gains · By Area</div>'
        + f'<h2>Impact areas for teams like {company}</h2>'
        + '</div>'
        + '<div class="bar-chart">'
        + '<div class="bar-row"><div class="bar-label">Operations</div><div class="bar-track"><div class="bar-fill" style="width:82%;background:#7c3aed">82%</div></div></div>'
        + '<div class="bar-row"><div class="bar-label">Admin</div><div class="bar-track"><div class="bar-fill" style="width:74%;background:#2563eb">74%</div></div></div>'
        + '<div class="bar-row"><div class="bar-label">Reporting</div><div class="bar-track"><div class="bar-fill" style="width:68%;background:#ec4899">68%</div></div></div>'
        + '<div class="bar-row"><div class="bar-label">Onboarding</div><div class="bar-track"><div class="bar-fill" style="width:91%;background:#7c3aed">91%</div></div></div>'
        + '</div>'
        # Strategic fit steps
        + '<div class="sec">'
        + '<div class="sec-lbl">Strategic Fit</div>'
        + f'<h2>Three things that change for {company}</h2>'
        + '</div>'
        + '<div class="steps">'
        + f'<div class="step"><div class="snum">1</div><div><div class="stitle">Eliminate {pain}</div><div class="sdesc">{product_name} automates the bottleneck your team is currently working around.</div></div></div>'
        + '<div class="step"><div class="snum">2</div><div><div class="stitle">Team productivity compounds</div><div class="sdesc">Teams stop spending time on manual work. Productivity rises measurably in the first quarter.</div></div></div>'
        + '<div class="step" style="margin-bottom:0"><div class="snum">3</div><div><div class="stitle">ROI shows up fast</div><div class="sdesc">14-day time-to-value means meaningful ROI that shows up in your next review cycle.</div></div></div>'
        + '</div>'
        # ROI
        + '<div class="roi">'
        + '<div class="roi-lbl">Executive ROI Summary</div>'
        + '<div class="roi-g">'
        + '<div class="ri"><div class="rn" style="color:#c4b5fd">18×</div><div class="rd">ROI</div></div>'
        + '<div class="ri"><div class="rn" style="color:#f9a8d4">43 days</div><div class="rd">Payback period</div></div>'
        + '<div class="ri"><div class="rn" style="color:#93c5fd">92%</div><div class="rd">Customer satisfaction</div></div>'
        + '</div></div>'
        # AI body
        + f'<div class="plain">{body_html}</div>'
        + _cta(product_url, company, product_name, "Book a 20-min executive call →")
        + _footer(sender_name, sender_title, product_name, sender_phone, product_url)
        + '</div>'
    )


# ═══════════════════════════════════════════════════════════════════
#  TEMPLATE 6 — CASE STUDY (Social Proof + Results)
# ═══════════════════════════════════════════════════════════════════

def _tpl_casestudy(ai_body, subject, first_name, company, title,
                   product_name, product_summary, product_url,
                   pain_points, demo_video_url,
                   sender_name, sender_title, sender_phone, role_cat):
    paras = [p.strip() for p in ai_body.strip().split("\n\n") if p.strip()]
    hook = paras[0] if paras else ""
    rest = paras[1:] if len(paras) > 1 else []
    rest_html = "".join(f"<p>{p}</p>" for p in rest)

    return _wrap(
        '<div class="shell">'
        + _header(product_name, first_name)
        # Hero
        + '<div class="hero">'
        + f'<div class="eyebrow">Customer Story · {company}-Sized Reference</div>'
        + f'<h1>How a team like <span class="vpk">{company}</span> went from<br><span class="vp">struggling to thriving</span> in one quarter.</h1>'
        + f'<p>{product_summary[:180]}</p>'
        + '</div>'
        # Quote from "customer"
        + '<div class="pnote">'
        + '<div class="pnote-lbl">The Situation</div>'
        + f'<blockquote>"{hook}"</blockquote>'
        + f'<div class="sig">— {sender_name or "Our team"}, {sender_title or "Growth"}</div>'
        + '</div>'
        # Results stats
        + '<div class="sec" style="padding-bottom:4px">'
        + '<div class="sec-lbl">The Results · One Quarter</div>'
        + '<h2>What was achieved in 90 days</h2>'
        + '</div>'
        + '<div class="stats">'
        + '<div class="stat"><div class="sv cp">3.2×</div><div class="sl">ROI achieved</div></div>'
        + '<div class="stat"><div class="sv cpk">+70%</div><div class="sl">Efficiency gain</div></div>'
        + '<div class="stat"><div class="sv cb">14 days</div><div class="sl">To first results</div></div>'
        + '</div>'
        # Progress bars — weekly ramp
        + '<div class="sec" style="padding-bottom:4px">'
        + '<div class="sec-lbl">Adoption · Week by Week</div>'
        + '<h2>The ramp from week 1 to week 12</h2>'
        + '</div>'
        + '<div class="prog-wrap">'
        + '<div class="pr"><div class="pr-row"><span class="pr-name">Week 2</span><span class="pr-val">Setup complete</span></div><div class="pr-track"><div class="pr-bar" style="width:15%;background:#7c3aed"></div></div></div>'
        + '<div class="pr"><div class="pr-row"><span class="pr-name">Week 4</span><span class="pr-val">First results</span></div><div class="pr-track"><div class="pr-bar" style="width:35%;background:#2563eb"></div></div></div>'
        + '<div class="pr"><div class="pr-row"><span class="pr-name">Week 8</span><span class="pr-val">Full adoption</span></div><div class="pr-track"><div class="pr-bar" style="width:70%;background:#ec4899"></div></div></div>'
        + '<div class="pr"><div class="pr-row"><span class="pr-name">Week 12</span><span class="pr-val">3.2× ROI</span></div><div class="pr-track"><div class="pr-bar" style="width:95%;background:#7c3aed"></div></div></div>'
        + '</div>'
        # Three key moves
        + '<div class="flow">'
        + '<div class="flow-lbl">Three Moves That Made the Difference</div>'
        + '<div class="flow-row">'
        + '<div class="fs"><div class="fi" style="background:#ede9fe">🎯</div><div class="ft">Focused</div><div class="fd">Identified key bottleneck</div></div>'
        + '<div class="fs"><div class="fi" style="background:#fce7f3">📡</div><div class="ft">Automated</div><div class="fd">AI eliminated manual work</div></div>'
        + '<div class="fs"><div class="fi" style="background:#dbeafe">🔄</div><div class="ft">Scaled</div><div class="fd">Team-wide in 2 weeks</div></div>'
        + '<div class="fs"><div class="fi" style="background:#ede9fe">🏆</div><div class="ft">3.2× ROI</div><div class="fd">In one quarter</div></div>'
        + '</div></div>'
        # ROI projection
        + '<div class="roi">'
        + f'<div class="roi-lbl">If {company} Got the Same Result</div>'
        + '<div class="roi-g">'
        + '<div class="ri"><div class="rn" style="color:#c4b5fd">3.2×</div><div class="rd">Projected ROI</div></div>'
        + '<div class="ri"><div class="rn" style="color:#f9a8d4">+70%</div><div class="rd">Efficiency</div></div>'
        + '<div class="ri"><div class="rn" style="color:#93c5fd">43 days</div><div class="rd">Payback period</div></div>'
        + '</div></div>'
        # AI rest body
        + f'<div class="plain">{rest_html}</div>'
        + _video(demo_video_url)
        + _cta(product_url, company, product_name, "Book your strategy call →")
        + _footer(sender_name, sender_title, product_name, sender_phone, product_url)
        + '</div>'
    )


# ═══════════════════════════════════════════════════════════════════
#  TEMPLATE POOL — Random selection per email type
# ═══════════════════════════════════════════════════════════════════

TEMPLATE_POOLS = {
    "cold_email":    [_tpl_cold_signal, _tpl_ceo_executive],
    "follow_up":     [_tpl_followup_benchmark, _tpl_casestudy],
    "breakup":       [_tpl_breakup_honest],
    "introduction":  [_tpl_intro_flow],
}


# ═══════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINTS
# ═══════════════════════════════════════════════════════════════════

def build_email_html(
    template_type: str, ai_body: str, subject: str,
    first_name: str, company: str, title: str,
    product_name: str, product_summary: str, product_url: str,
    pain_points: list, demo_video_url: str,
    sender_name: str, sender_title: str, sender_phone: str,
    role_category: str,
) -> str:
    """Build premium HTML email — randomly picks from template pool for A/B variation."""
    pool = TEMPLATE_POOLS.get(template_type, TEMPLATE_POOLS["cold_email"])
    builder = random.choice(pool)
    return builder(
        ai_body, subject, first_name, company, title,
        product_name, product_summary or "", product_url or "",
        pain_points or [], demo_video_url or "",
        sender_name or "", sender_title or "", sender_phone or "",
        role_category or "general",
    )


# Backward compatibility aliases
def build_cold_email_html(ai_body, subject, first_name, company, title,
                          product_name, product_summary, product_url,
                          pain_points, demo_video_url,
                          sender_name, sender_title, sender_phone, role_category):
    return _tpl_cold_signal(ai_body, subject, first_name, company, title,
                            product_name, product_summary, product_url,
                            pain_points, demo_video_url,
                            sender_name, sender_title, sender_phone, role_category)


def build_follow_up_html(ai_body, first_name, company,
                         product_name, product_url, demo_video_url,
                         sender_name, sender_title, sender_phone):
    return _tpl_followup_benchmark(ai_body, "", first_name, company, "",
                                   product_name, "", product_url,
                                   [], demo_video_url,
                                   sender_name, sender_title, sender_phone, "general")


def build_introduction_html(ai_body, subject, first_name, company, title,
                            product_name, product_summary, product_url,
                            demo_video_url,
                            sender_name, sender_title, sender_phone):
    return _tpl_intro_flow(ai_body, subject, first_name, company, title,
                           product_name, product_summary, product_url,
                           [], demo_video_url,
                           sender_name, sender_title, sender_phone, "general")


def build_breakup_html(ai_body, first_name, company,
                       product_name, product_url,
                       sender_name, sender_title, sender_phone):
    return _tpl_breakup_honest(ai_body, "", first_name, company, "",
                               product_name, "", product_url,
                               [], "",
                               sender_name, sender_title, sender_phone, "general")


def get_subject_line(
    template_type: str, role_category: str,
    first_name: str, company: str, product_name: str,
    sender_name: str, pain_points: list,
) -> str:
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
