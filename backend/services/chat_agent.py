"""Conversational prospecting agent for ProspectIQ.

A Gemini-powered agent loop. Each turn the model is asked to choose ONE next
step (respond / analyze_product / find_leads / research_company). Tools are
executed server-side and their results are fed back to the model until it
produces a final natural-language reply for the user.
"""
import asyncio
import json
import logging
from datetime import datetime

import google.generativeai as genai

from config import get_settings
from database import get_db
from models import new_campaign, new_lead, doc_to_dict
from services.scraper import scrape_website
from services.ai_service import extract_product_info
from services.lead_finder import find_leads_apollo

logger = logging.getLogger(__name__)
settings = get_settings()

if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

MAX_STEPS = 5
LEAD_LIMIT = 25

SYSTEM_PROMPT = """You are the ProspectIQ Assistant, a friendly and capable AI \
sales prospecting assistant. You help users find prospects, research companies, \
draft outreach, and prepare for meetings.

You operate as a tool-using agent. Available tools:
- analyze_product: Given a product website URL, scrapes it and builds an ideal \
customer profile (ICP), target industries, target roles and a list of target \
company domains. Creates a campaign the user can continue working with.
- find_leads: Finds real contacts (leads) at target company domains via Apollo. \
Use after a product is analyzed, or when the user supplies company domains.
- research_company: Produces a concise research brief on a specific company so \
the user can prepare for outreach or a meeting.

Behaviour rules:
- Be concise, warm and professional. Short paragraphs. Avoid heavy formatting.
- If the user gives a product URL/website and wants prospects, analyze_product.
- If a product is already analyzed (see KNOWN CONTEXT) and the user wants \
leads/contacts/prospects, use find_leads.
- If the user asks about a particular company, use research_company.
- If the request is ambiguous (you don't know which product, which company, or \
which roles), do NOT guess. Use action "respond" to ask ONE short clarifying \
question, optionally offering 2-3 numbered choices.
- After a tool runs, look at TOOL RESULTS THIS TURN and either run another tool \
or use action "respond" to summarise the outcome for the user clearly."""


def _model():
    return genai.GenerativeModel(settings.gemini_model)


async def _generate(prompt: str) -> str:
    """Run a blocking Gemini call off the event loop and return its text."""
    model = _model()
    resp = await asyncio.to_thread(model.generate_content, prompt)
    try:
        return (resp.text or "").strip()
    except Exception:
        return ""


def _extract_json(text: str) -> dict:
    """Best-effort extraction of a single JSON object from a model response."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _build_router_prompt(messages: list, context: dict, tool_log: list) -> str:
    convo = "\n".join(
        f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages
    ) or "(no messages yet)"
    ctx = json.dumps(context, indent=2, default=str) if context else "(nothing known yet)"
    log = "\n".join(tool_log) if tool_log else "(no tools run yet this turn)"
    return f"""{SYSTEM_PROMPT}

CONVERSATION SO FAR:
{convo}

KNOWN CONTEXT (facts established earlier this session):
{ctx}

TOOL RESULTS THIS TURN:
{log}

Decide the single next step. Respond with ONLY a JSON object, no markdown:
{{
  "action": "respond" | "analyze_product" | "find_leads" | "research_company",
  "product_url": "<website url, only when action=analyze_product>",
  "domains": ["company.com"],
  "roles": ["VP of Sales"],
  "company": "<company name or domain, only when action=research_company>",
  "message": "<the text to show the user, REQUIRED when action=respond>"
}}

For find_leads, domains and roles are optional - leave them empty to reuse the \
analyzed product's target domains and roles. Always provide "message" when the \
action is "respond"."""


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------
async def _tool_analyze_product(url: str, context: dict) -> dict:
    """Scrape a product URL, extract an ICP, and create a campaign."""
    url = (url or "").strip()
    if not url:
        return {"summary_for_model": "No product URL was provided."}
    if not url.startswith("http"):
        url = "https://" + url

    try:
        scrape = await scrape_website(url)
        info = await extract_product_info(scrape.get("content", ""))
    except Exception as exc:
        logger.warning(f"analyze_product failed for {url}: {exc}")
        return {"summary_for_model": f"Could not analyze {url}: {exc}"}

    db = get_db()
    campaign = new_campaign(url)
    campaign.update({
        "product_name": info.get("product_name", "") or url,
        "product_summary": info.get("product_summary", ""),
        "ideal_customer_profile": info.get("ideal_customer_profile", {}) or {},
        "industries": info.get("industries", []) or [],
        "roles": info.get("roles", []) or [],
        "pain_points": info.get("pain_points", []) or [],
        "target_domains": info.get("target_domains", []) or [],
        "demo_video_url": scrape.get("demo_video_url", "") or info.get("demo_video_url", ""),
        "product_phone": scrape.get("phone", "") or info.get("phone", ""),
        "contact_emails": scrape.get("emails", []),
        "social_links": scrape.get("social_links", {}),
        "calendly_url": scrape.get("calendly_url", ""),
        "demo_booking_url": scrape.get("demo_booking_url", ""),
        "status": "finding_leads",
        "updated_at": datetime.utcnow(),
    })
    await db.campaigns.insert_one(campaign)

    context["campaign_id"] = campaign["_id"]
    context["product_name"] = campaign["product_name"]
    context["roles"] = campaign["roles"]
    context["target_domains"] = campaign["target_domains"]

    card = {
        "id": campaign["_id"],
        "product_name": campaign["product_name"],
        "product_summary": campaign["product_summary"],
        "industries": campaign["industries"],
        "roles": campaign["roles"],
        "pain_points": campaign["pain_points"],
        "target_domains": campaign["target_domains"],
    }
    summary = (
        f"Analyzed '{campaign['product_name']}'. "
        f"Industries: {', '.join(campaign['industries'][:5])}. "
        f"Target roles: {', '.join(campaign['roles'][:5])}. "
        f"Found {len(campaign['target_domains'])} candidate target company domains. "
        f"campaign_id={campaign['_id']}."
    )
    return {"campaign": card, "summary_for_model": summary}


async def _tool_find_leads(domains, roles, context: dict) -> dict:
    """Find leads via Apollo and persist them to the active campaign."""
    db = get_db()
    campaign_id = context.get("campaign_id")
    campaign = None
    if campaign_id:
        campaign = await db.campaigns.find_one({"_id": campaign_id})

    domains = [d for d in (domains or []) if d] or \
        (campaign or {}).get("target_domains", []) or context.get("target_domains", [])
    roles = [r for r in (roles or []) if r] or \
        (campaign or {}).get("roles", []) or context.get("roles", [])

    if not domains:
        return {
            "summary_for_model": "No target company domains are available yet. "
            "Either analyze a product first, or ask the user for company domains.",
            "leads": [],
        }

    try:
        raw = await find_leads_apollo(domains, roles, LEAD_LIMIT)
    except Exception as exc:
        logger.warning(f"find_leads failed: {exc}")
        return {"summary_for_model": f"Lead search failed: {exc}", "leads": []}

    leads_out = []
    for r in raw:
        if campaign_id and r.get("email"):
            existing = await db.leads.find_one(
                {"campaign_id": campaign_id, "email": r["email"]}
            )
            if existing:
                continue
            lead = new_lead(
                campaign_id=campaign_id,
                first_name=r.get("first_name", ""),
                last_name=r.get("last_name", ""),
                email=r.get("email", ""),
                company=r.get("company", ""),
                title=r.get("title", ""),
                linkedin_url=r.get("linkedin_url", ""),
                domain=r.get("domain", ""),
                status="raw",
            )
            await db.leads.insert_one(lead)
        leads_out.append({
            "name": (r.get("first_name", "") + " " + r.get("last_name", "")).strip(),
            "title": r.get("title", ""),
            "company": r.get("company", ""),
            "email": r.get("email", ""),
            "linkedin_url": r.get("linkedin_url", ""),
        })

    context["leads_found"] = len(leads_out)
    summary = (
        f"Found {len(leads_out)} leads across {len(domains)} domains "
        f"({', '.join(domains[:5])}{'...' if len(domains) > 5 else ''})."
    )
    if campaign_id:
        summary += f" Saved to campaign {campaign_id}."
    return {"leads": leads_out, "summary_for_model": summary}


async def _tool_research_company(company: str, context: dict) -> dict:
    """Produce a concise research brief on a company."""
    company = (company or "").strip()
    if not company:
        return {"summary_for_model": "No company was specified."}

    site_text = ""
    looks_like_domain = "." in company and " " not in company
    if looks_like_domain:
        try:
            scrape = await scrape_website(
                company if company.startswith("http") else "https://" + company
            )
            site_text = (scrape.get("content", "") or "")[:6000]
        except Exception as exc:
            logger.warning(f"research_company scrape failed for {company}: {exc}")

    prompt = (
        f"Write a concise research brief about the company '{company}' for a "
        f"salesperson who is about to reach out to them. Cover: what the company "
        f"does, its likely size and industry, plausible pain points, and one "
        f"suggested outreach angle. 4-6 short sentences, plain text, no headings.\n\n"
    )
    prompt += (
        f"Use this content from their website:\n{site_text}"
        if site_text else
        "Base it on your general knowledge of this company."
    )

    brief = await _generate(prompt)
    if not brief:
        brief = f"I couldn't gather details on {company} right now."
    context["last_researched_company"] = company
    return {
        "research": {"company": company, "brief": brief},
        "summary_for_model": brief[:600],
    }


# --------------------------------------------------------------------------
# Agent loop
# --------------------------------------------------------------------------
async def run_chat(messages: list, context: dict) -> dict:
    """Run the agent for the latest user message. Returns reply/context/data."""
    context = dict(context or {})
    data: dict = {}
    tool_log: list = []

    if not settings.gemini_api_key:
        return {
            "reply": "The assistant isn't configured yet - a Gemini API key is "
                     "missing from the server's .env file. Once that's set I can "
                     "research products, find leads and help with outreach.",
            "context": context,
            "data": data,
        }

    for _ in range(MAX_STEPS):
        try:
            raw = await _generate(_build_router_prompt(messages, context, tool_log))
            decision = _extract_json(raw)
        except Exception as exc:
            logger.warning(f"router step failed: {exc}")
            return {
                "reply": "Sorry, I had trouble processing that. Could you rephrase?",
                "context": context,
                "data": data,
            }

        action = (decision.get("action") or "respond").strip()

        if action == "respond":
            reply = decision.get("message") or "How can I help with your prospecting today?"
            return {"reply": reply, "context": context, "data": data}

        if action == "analyze_product":
            result = await _tool_analyze_product(decision.get("product_url", ""), context)
            if result.get("campaign"):
                data["campaign"] = result["campaign"]
            tool_log.append("analyze_product -> " + result.get("summary_for_model", ""))

        elif action == "find_leads":
            result = await _tool_find_leads(
                decision.get("domains"), decision.get("roles"), context
            )
            if result.get("leads"):
                data["leads"] = result["leads"]
            tool_log.append("find_leads -> " + result.get("summary_for_model", ""))

        elif action == "research_company":
            result = await _tool_research_company(decision.get("company", ""), context)
            if result.get("research"):
                data["research"] = result["research"]
            tool_log.append("research_company -> " + result.get("summary_for_model", ""))

        else:
            return {
                "reply": decision.get("message")
                or "I'm not sure how to help with that yet - could you give me more detail?",
                "context": context,
                "data": data,
            }

    # Safety net: ran out of steps - ask the model for a closing summary.
    closing = await _generate(
        _build_router_prompt(messages, context, tool_log)
        + "\n\nWrite a concise, friendly final reply to the user summarising what "
        "you did and the results. Plain text only, no JSON."
    )
    return {
        "reply": closing or "Here's what I found - let me know what you'd like to do next.",
        "context": context,
        "data": data,
    }
