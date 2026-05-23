"""
ProspectIQ Agent System
-----------------------
Four specialized AI agents that work together:

1. ReplyAgent      — Monitors replies, understands intent, auto-responds
2. MailAgent       — Sends emails, tracks no-replies, triggers follow-ups
3. PerformanceAgent — Analyzes campaign metrics, suggests optimizations
4. ContextAgent    — Maintains business context for personalization
"""
import json
from datetime import datetime, timedelta
from database import get_db
from services.ai_service import _get_model


# ─── Agent activity log ────────────────────────────────────────────────
def _log(agent: str, campaign_id: str, action: str, detail: str = ""):
    """Create an agent activity log entry."""
    from models import generate_id
    return {
        "_id": generate_id(),
        "agent": agent,
        "campaign_id": campaign_id,
        "action": action,
        "detail": detail,
        "created_at": datetime.utcnow(),
    }


# ========================================================================
#  1. REPLY AGENT — Understands replies and auto-responds
# ========================================================================
class ReplyAgent:
    """
    Reads incoming replies, classifies intent with fine-grained understanding,
    and generates the perfect auto-response including scheduling links,
    demo videos, pricing info, etc.
    """
    NAME = "reply_agent"

    INTENT_MAP = {
        "schedule_call": "Lead wants to schedule a call / meeting",
        "demo_request": "Lead wants a product demo or video walkthrough",
        "pricing": "Lead is asking about pricing or plans",
        "interested": "Lead is interested, wants more info",
        "question": "Lead has a specific question",
        "objection": "Lead has an objection or concern",
        "not_interested": "Lead is not interested",
        "unsubscribe": "Lead wants to be removed from emails",
        "out_of_office": "Auto-reply / out of office",
        "referral": "Lead is referring to someone else in their org",
    }

    @staticmethod
    async def classify_intent(reply_body: str) -> dict:
        """Deep intent classification with confidence and sub-intent."""
        model = _get_model()
        prompt = f"""Analyze this email reply and classify the sender's intent.

Reply:
{reply_body[:3000]}

Return a JSON object:
{{
  "intent": one of [{', '.join(ReplyAgent.INTENT_MAP.keys())}],
  "confidence": 0.0-1.0,
  "sentiment": "positive" | "neutral" | "negative",
  "urgency": "high" | "medium" | "low",
  "key_points": ["brief point 1", "brief point 2"],
  "suggested_action": "brief description of what to do"
}}

Return ONLY valid JSON."""

        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"intent": "question", "confidence": 0.5, "sentiment": "neutral",
                    "urgency": "medium", "key_points": [], "suggested_action": "Review manually"}

    @staticmethod
    async def generate_response(reply_body: str, intent_data: dict, campaign: dict, lead: dict) -> dict:
        """Generate the perfect auto-response based on intent and campaign context."""
        model = _get_model()
        intent = intent_data.get("intent", "question")

        # Build context-rich response resources
        calendly = campaign.get("calendly_url", "")
        demo_booking = campaign.get("demo_booking_url", "")
        demo_video = campaign.get("demo_video_url", "")
        product_name = campaign.get("product_name", "")
        product_summary = campaign.get("product_summary", "")
        product_url = campaign.get("product_url", "")
        sender_name = campaign.get("sender_name", "")
        sender_title = campaign.get("sender_title", "")
        sender_phone = campaign.get("sender_phone", "") or campaign.get("product_phone", "")
        pain_points = campaign.get("pain_points", [])

        # Intent-specific instructions
        intent_instructions = {
            "schedule_call": f"""They want to connect/schedule a call.
- Include booking link: {calendly or demo_booking or '[BOOKING_LINK]'}
- Suggest 2-3 time slots this week
- Keep it warm and enthusiastic""",
            "demo_request": f"""They want a demo.
- {'Share demo video: ' + demo_video if demo_video else 'Offer to schedule a live demo'}
- Include booking link: {calendly or demo_booking or '[BOOKING_LINK]'}
- Highlight what they will see in the demo""",
            "pricing": f"""They are asking about pricing.
- Share general pricing overview or direct them to pricing page
- Emphasize value and ROI
- Suggest a quick call to discuss their specific needs
- {'Booking link: ' + (calendly or demo_booking) if (calendly or demo_booking) else ''}""",
            "interested": f"""They are interested and want more info.
- Share 2-3 key benefits relevant to their role ({lead.get('title', '')})
- Include a link to learn more: {product_url}
- Suggest a next step (demo, call, or case study)""",
            "question": f"""They have a specific question. Answer it using:
- Product: {product_name} — {product_summary}
- Pain points solved: {', '.join(pain_points[:3])}
- Be specific and helpful
- End with a soft CTA""",
            "objection": """They have a concern or objection.
- Acknowledge their concern respectfully
- Address it with data/facts from product info
- Share a relevant case study angle
- Don't be pushy""",
            "not_interested": """They said no.
- Thank them graciously
- Leave the door open
- Keep it to 2-3 sentences max
- No hard sell""",
            "unsubscribe": """They want off the list.
- Confirm removal immediately
- Apologize briefly
- 1-2 sentences only""",
            "out_of_office": """They're out of office.
- Note their return date if mentioned
- Plan to follow up after they return
- No need to send a reply now""",
            "referral": """They're referring someone else.
- Thank them for the referral
- Ask for the referred person's name/email if not provided
- Keep relationship warm""",
        }

        prompt = f"""Draft a reply to this email.

Their reply:
{reply_body[:2000]}

Intent analysis: {json.dumps(intent_data)}

Product context:
- Product: {product_name}
- Summary: {product_summary}
- URL: {product_url}

Sender context:
- From: {sender_name}, {sender_title}
- Phone: {sender_phone}

Lead: {lead.get('first_name', '')} {lead.get('last_name', '')}, {lead.get('title', '')} at {lead.get('company', '')}

SPECIFIC INSTRUCTIONS:
{intent_instructions.get(intent, 'Reply helpfully and professionally.')}

Rules:
- Professional, warm tone
- Personalized to their name and role
- Include specific links/resources when relevant
- Sign off as {sender_name or 'the team'}
- Keep it concise (3-6 sentences unless answering a complex question)

Return ONLY the reply email text."""

        response = model.generate_content(prompt)
        reply_text = response.text.strip()

        return {
            "reply_text": reply_text,
            "intent": intent,
            "confidence": intent_data.get("confidence", 0.5),
            "auto_actions": ReplyAgent._determine_actions(intent, campaign),
        }

    @staticmethod
    def _determine_actions(intent: str, campaign: dict) -> list:
        """Determine automated actions based on intent."""
        actions = []
        if intent == "schedule_call":
            if campaign.get("calendly_url"):
                actions.append({"type": "include_link", "label": "Calendly", "url": campaign["calendly_url"]})
            actions.append({"type": "update_lead_status", "status": "converted"})
        elif intent == "demo_request":
            if campaign.get("demo_video_url"):
                actions.append({"type": "include_link", "label": "Demo Video", "url": campaign["demo_video_url"]})
            if campaign.get("demo_booking_url"):
                actions.append({"type": "include_link", "label": "Book Demo", "url": campaign["demo_booking_url"]})
            actions.append({"type": "update_lead_status", "status": "converted"})
        elif intent == "interested":
            actions.append({"type": "update_lead_status", "status": "converted"})
        elif intent == "not_interested":
            actions.append({"type": "update_lead_status", "status": "dropped"})
            actions.append({"type": "add_suppression"})
        elif intent == "unsubscribe":
            actions.append({"type": "add_suppression"})
            actions.append({"type": "update_lead_status", "status": "dropped"})
        elif intent == "out_of_office":
            actions.append({"type": "schedule_followup", "delay_days": 7})
        elif intent == "referral":
            actions.append({"type": "flag_for_review", "reason": "Referral — may need new lead"})
        return actions

    @staticmethod
    async def process_reply(campaign_id: str, lead_id: str, reply_body: str, from_email: str, subject: str) -> dict:
        """Full pipeline: classify → respond → execute actions → log."""
        db = get_db()
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        lead = await db.leads.find_one({"_id": lead_id})
        if not campaign or not lead:
            return {"error": "Campaign or lead not found"}

        # 1. Deep intent classification
        intent_data = await ReplyAgent.classify_intent(reply_body)

        # 2. Generate smart response
        response_data = await ReplyAgent.generate_response(reply_body, intent_data, campaign, lead)

        # 3. Save reply to DB
        from models import new_reply, new_suppression, generate_id
        reply_doc = new_reply(
            lead_id=lead_id,
            from_email=from_email,
            subject=subject,
            body=reply_body,
            intent=intent_data["intent"],
            ai_draft_reply=response_data["reply_text"],
        )
        reply_doc["intent_data"] = intent_data
        reply_doc["auto_actions"] = response_data["auto_actions"]
        await db.replies.insert_one(reply_doc)

        # 4. Execute auto-actions
        for action in response_data["auto_actions"]:
            if action["type"] == "update_lead_status":
                await db.leads.update_one(
                    {"_id": lead_id},
                    {"$set": {"status": action["status"], "updated_at": datetime.utcnow()}}
                )
            elif action["type"] == "add_suppression":
                existing = await db.suppression_list.find_one({"email": lead["email"]})
                if not existing:
                    await db.suppression_list.insert_one(new_suppression(lead["email"], intent_data["intent"]))
                await db.leads.update_one(
                    {"_id": lead_id},
                    {"$set": {"is_suppressed": True, "suppression_reason": intent_data["intent"]}}
                )
            elif action["type"] == "schedule_followup":
                delay = action.get("delay_days", 7)
                await db.agent_tasks.insert_one({
                    "_id": generate_id(),
                    "agent": "mail_agent",
                    "campaign_id": campaign_id,
                    "lead_id": lead_id,
                    "task": "follow_up_after_ooo",
                    "scheduled_at": datetime.utcnow() + timedelta(days=delay),
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                })

        # 5. Log activity
        await db.agent_logs.insert_one(_log(
            ReplyAgent.NAME, campaign_id, f"processed_reply:{intent_data['intent']}",
            f"Lead {lead.get('first_name', '')} {lead.get('last_name', '')} — {intent_data.get('suggested_action', '')}"
        ))

        # 6. Mark lead as replied
        await db.leads.update_one(
            {"_id": lead_id},
            {"$set": {"status": "replied", "updated_at": datetime.utcnow()}}
        )

        from models import doc_to_dict
        return {
            "reply": doc_to_dict(reply_doc),
            "intent_data": intent_data,
            "auto_response": response_data["reply_text"],
            "actions_taken": response_data["auto_actions"],
        }


# ========================================================================
#  2. MAIL AGENT — Sends emails, tracks no-replies, triggers follow-ups
# ========================================================================
class MailAgent:
    """
    Handles the outreach pipeline:
    - Sends approved emails
    - Tracks which leads haven't replied
    - Auto-triggers next sequence steps
    - Manages send scheduling
    """
    NAME = "mail_agent"

    @staticmethod
    async def get_pending_sends(campaign_id: str) -> list:
        """Get all approved but unsent steps ready to go."""
        db = get_db()
        steps = await db.outreach_steps.find({
            "status": "approved",
        }).to_list(500)

        # Filter by campaign via lead
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id, "is_suppressed": False}, {"_id": 1}
        )]
        return [s for s in steps if s["lead_id"] in lead_ids]

    @staticmethod
    async def get_no_reply_leads(campaign_id: str, days_since_sent: int = 3) -> list:
        """Find leads who were sent an email but haven't replied."""
        db = get_db()
        cutoff = datetime.utcnow() - timedelta(days=days_since_sent)

        leads = await db.leads.find({
            "campaign_id": campaign_id,
            "status": {"$in": ["enrolled", "contacted"]},
            "is_suppressed": False,
        }).to_list(500)

        no_reply = []
        for lead in leads:
            # Check if there's a sent step older than cutoff with no reply
            sent_steps = await db.outreach_steps.find({
                "lead_id": lead["_id"],
                "status": "sent",
                "sent_at": {"$lt": cutoff},
            }).sort("sent_at", -1).to_list(1)

            if sent_steps:
                # Check if a reply exists after the last sent step
                reply = await db.replies.find_one({
                    "lead_id": lead["_id"],
                    "received_at": {"$gt": sent_steps[0]["sent_at"]},
                })
                if not reply:
                    # Check what step they're on
                    all_steps = await db.outreach_steps.find(
                        {"lead_id": lead["_id"]}
                    ).sort("step_number", 1).to_list(20)
                    sent_count = len([s for s in all_steps if s["status"] == "sent"])
                    total_count = len(all_steps)
                    next_step = next((s for s in all_steps if s["status"] in ("pending", "approved")), None)

                    from models import doc_to_dict
                    no_reply.append({
                        "lead": doc_to_dict(lead),
                        "last_sent": doc_to_dict(sent_steps[0]),
                        "days_waiting": (datetime.utcnow() - sent_steps[0]["sent_at"]).days,
                        "sent_count": sent_count,
                        "total_steps": total_count,
                        "next_step": doc_to_dict(next_step) if next_step else None,
                    })

        return no_reply

    @staticmethod
    async def auto_send_next(campaign_id: str) -> dict:
        """Auto-approve and send the next step for no-reply leads."""
        from services.email_sender import send_step as send_step_email
        db = get_db()
        no_reply = await MailAgent.get_no_reply_leads(campaign_id)
        advanced = 0
        sent_ok = 0
        sent_fail = 0
        skipped = 0

        for item in no_reply:
            next_step = item.get("next_step")
            if next_step and next_step["status"] in ("pending", "approved"):
                # Auto-approve if pending
                if next_step["status"] == "pending":
                    await db.outreach_steps.update_one(
                        {"_id": next_step["id"]},
                        {"$set": {"status": "approved", "approved": True, "updated_at": datetime.utcnow()}}
                    )
                advanced += 1

                # Actually send the email
                if next_step.get("step_type") == "email":
                    result = await send_step_email(next_step["id"])
                    if "error" in result:
                        sent_fail += 1
                    else:
                        sent_ok += 1
            else:
                skipped += 1

        await db.agent_logs.insert_one(_log(
            MailAgent.NAME, campaign_id, "auto_advance_and_send",
            f"Advanced {advanced}, sent {sent_ok}, failed {sent_fail}, skipped {skipped}"
        ))

        return {
            "advanced": advanced,
            "sent": sent_ok,
            "failed": sent_fail,
            "skipped": skipped,
            "no_reply_count": len(no_reply),
        }

    @staticmethod
    async def get_campaign_mail_status(campaign_id: str) -> dict:
        """Get mail send status overview for a campaign."""
        db = get_db()
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id}, {"_id": 1}
        )]
        if not lead_ids:
            return {"total_steps": 0, "pending": 0, "approved": 0, "sent": 0}

        pipeline = [
            {"$match": {"lead_id": {"$in": lead_ids}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        results = {}
        async for doc in db.outreach_steps.aggregate(pipeline):
            results[doc["_id"]] = doc["count"]

        return {
            "total_steps": sum(results.values()),
            "pending": results.get("pending", 0),
            "approved": results.get("approved", 0),
            "sent": results.get("sent", 0),
        }


# ========================================================================
#  3. PERFORMANCE AGENT — Analyzes metrics, suggests optimizations
# ========================================================================
class PerformanceAgent:
    """
    Analyzes campaign performance and provides AI-powered recommendations:
    - Which email types get the best reply rates
    - Which roles respond most
    - Optimal send times
    - Sequence optimization suggestions
    """
    NAME = "performance_agent"

    @staticmethod
    async def analyze_campaign(campaign_id: str) -> dict:
        """Full performance analysis with AI recommendations."""
        db = get_db()
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not campaign:
            return {"error": "Campaign not found"}

        lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]
        if not lead_ids:
            return {"metrics": {}, "recommendations": ["No leads found. Start by finding leads."]}

        # Gather metrics
        steps = await db.outreach_steps.find({"lead_id": {"$in": lead_ids}}).to_list(2000)
        replies = await db.replies.find({"lead_id": {"$in": lead_ids}}).to_list(500)
        leads = await db.leads.find({"campaign_id": campaign_id}).to_list(500)

        total_sent = len([s for s in steps if s["status"] == "sent"])
        total_replied = len(replies)
        reply_rate = round((total_replied / total_sent * 100) if total_sent > 0 else 0, 1)

        # By template type
        by_type = {}
        for s in steps:
            t = s.get("template_type", "cold_email")
            if t not in by_type:
                by_type[t] = {"sent": 0, "replied": 0}
            if s["status"] == "sent":
                by_type[t]["sent"] += 1

        reply_lead_ids = {r["lead_id"] for r in replies}
        for s in steps:
            if s["lead_id"] in reply_lead_ids and s["status"] == "sent":
                t = s.get("template_type", "cold_email")
                by_type[t]["replied"] += 1

        for t in by_type:
            sent = by_type[t]["sent"]
            by_type[t]["reply_rate"] = round((by_type[t]["replied"] / sent * 100) if sent > 0 else 0, 1)

        # By role
        by_role = {}
        for lead in leads:
            role = lead.get("title", "Unknown")
            status = lead.get("status", "raw")
            if role not in by_role:
                by_role[role] = {"total": 0, "replied": 0, "converted": 0}
            by_role[role]["total"] += 1
            if status == "replied":
                by_role[role]["replied"] += 1
            if status == "converted":
                by_role[role]["converted"] += 1

        # Intent breakdown
        intent_counts = {}
        for r in replies:
            intent = r.get("intent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        metrics = {
            "total_leads": len(leads),
            "total_sent": total_sent,
            "total_replied": total_replied,
            "reply_rate": reply_rate,
            "by_type": by_type,
            "by_role": by_role,
            "intent_breakdown": intent_counts,
            "conversion_rate": round(
                len([l for l in leads if l["status"] == "converted"]) / len(leads) * 100, 1
            ) if leads else 0,
        }

        # AI recommendations
        recommendations = await PerformanceAgent._get_ai_recommendations(metrics, campaign)

        await db.agent_logs.insert_one(_log(
            PerformanceAgent.NAME, campaign_id, "analysis",
            f"Reply rate: {reply_rate}%, {total_replied} replies from {total_sent} sent"
        ))

        return {"metrics": metrics, "recommendations": recommendations}

    @staticmethod
    async def _get_ai_recommendations(metrics: dict, campaign: dict) -> list:
        """Get AI-powered recommendations based on campaign performance."""
        model = _get_model()
        prompt = f"""Analyze this email campaign performance and give 3-5 specific, actionable recommendations.

Campaign: {campaign.get('product_name', '')}
Product: {campaign.get('product_summary', '')}

Performance Metrics:
{json.dumps(metrics, indent=2, default=str)}

Give recommendations as a JSON array of objects:
[
  {{"title": "Short title", "description": "Detailed recommendation", "priority": "high|medium|low", "category": "content|timing|targeting|sequence"}}
]

Focus on:
- Which email types work best and what to double down on
- Which roles respond most and how to adjust targeting
- Sequence timing optimizations
- Content improvements based on reply patterns

Return ONLY valid JSON array."""

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(text)
        except Exception:
            return [{"title": "Gather more data", "description": "Send more emails to get meaningful metrics.",
                     "priority": "high", "category": "sequence"}]


# ========================================================================
#  4. CONTEXT AGENT — Builds & maintains business context
# ========================================================================
class ContextAgent:
    """
    Maintains a deep understanding of the client's business:
    - Product knowledge base
    - Competitor analysis
    - FAQ generation
    - Objection handling playbook
    """
    NAME = "context_agent"

    @staticmethod
    async def build_context(campaign_id: str) -> dict:
        """Build comprehensive business context from campaign data."""
        db = get_db()
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not campaign:
            return {"error": "Campaign not found"}

        model = _get_model()
        prompt = f"""Analyze this product/business and create a comprehensive context document.

Product: {campaign.get('product_name', '')}
URL: {campaign.get('product_url', '')}
Summary: {campaign.get('product_summary', '')}
ICP: {json.dumps(campaign.get('ideal_customer_profile', {}))}
Industries: {campaign.get('industries', [])}
Target Roles: {campaign.get('roles', [])}
Pain Points: {campaign.get('pain_points', [])}

Create a JSON object:
{{
  "elevator_pitch": "2-sentence pitch",
  "value_propositions": ["value prop 1", "value prop 2", "value prop 3"],
  "competitive_advantages": ["advantage 1", "advantage 2"],
  "common_objections": [
    {{"objection": "text", "response": "how to handle it"}}
  ],
  "faq": [
    {{"question": "common question", "answer": "answer"}}
  ],
  "use_cases": [
    {{"role": "target role", "scenario": "how they use it", "benefit": "key benefit"}}
  ],
  "keywords": ["important product keywords"],
  "tone_guide": "recommended communication tone description"
}}

Return ONLY valid JSON."""

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            context = json.loads(text)
        except Exception:
            context = {
                "elevator_pitch": campaign.get("product_summary", ""),
                "value_propositions": campaign.get("pain_points", []),
                "competitive_advantages": [],
                "common_objections": [],
                "faq": [],
                "use_cases": [],
                "keywords": [],
                "tone_guide": "Professional and consultative",
            }

        # Store context
        await db.campaigns.update_one(
            {"_id": campaign_id},
            {"$set": {"business_context": context, "updated_at": datetime.utcnow()}}
        )

        await db.agent_logs.insert_one(_log(
            ContextAgent.NAME, campaign_id, "build_context",
            f"Generated {len(context.get('faq', []))} FAQs, {len(context.get('common_objections', []))} objections"
        ))

        return context

    @staticmethod
    async def get_context(campaign_id: str) -> dict:
        """Get stored business context for a campaign."""
        db = get_db()
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not campaign:
            return {}
        return campaign.get("business_context", {})

    @staticmethod
    async def answer_question(campaign_id: str, question: str) -> str:
        """Answer a question using the business context — used by Reply Agent."""
        db = get_db()
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not campaign:
            return "I don't have enough context to answer that."

        context = campaign.get("business_context", {})
        model = _get_model()
        prompt = f"""Answer this question about {campaign.get('product_name', 'our product')} using the context below.

Question: {question}

Product Context:
- Summary: {campaign.get('product_summary', '')}
- Value Props: {json.dumps(context.get('value_propositions', []))}
- FAQ: {json.dumps(context.get('faq', []))}
- Objection Handling: {json.dumps(context.get('common_objections', []))}
- Use Cases: {json.dumps(context.get('use_cases', []))}

Rules:
- Be specific and helpful
- Use facts from the context
- Keep it concise (2-4 sentences)
- Professional tone

Return ONLY the answer text."""

        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return "I'd be happy to help with that question. Let me connect you with our team for a detailed answer."


# ========================================================================
#  5. RESEARCH AGENT — Deep-dives companies and leads for intel
# ========================================================================
class ResearchAgent:
    """
    Researches companies and individual leads to fuel personalization:
    - Scrapes company websites for intel (funding, tech stack, news)
    - Generates personalization hooks (conversation starters)
    - Stores research on lead records for the Personalization Agent to use
    - Batch-researches all leads in a campaign
    """
    NAME = "research_agent"

    @staticmethod
    async def research_company(domain: str) -> dict:
        """Scrape and AI-analyze a company domain for outreach intel."""
        from services.scraper import scrape_website
        model = _get_model()

        try:
            scraped = await scrape_website(f"https://{domain}")
            content = scraped.get("content", "")[:6000]
        except Exception:
            content = f"Company at {domain}"

        prompt = f"""Research this company and extract outreach-relevant intel.

Domain: {domain}
Website content:
{content}

Return a JSON object:
{{
  "company_name": "official company name",
  "industry": "primary industry",
  "employee_count_estimate": "e.g. 50-200",
  "founding_year": "year or empty string",
  "hq_location": "city, country or empty string",
  "tech_stack": ["technology 1", "technology 2"],
  "recent_news": ["recent event or milestone 1", "recent event or milestone 2"],
  "funding_stage": "e.g. Series B or bootstrapped or unknown",
  "key_products": ["product or feature 1"],
  "pain_points_likely": ["likely pain point 1", "likely pain point 2"],
  "personalization_hooks": [
    "Hook 1: specific conversation starter tied to something real about this company",
    "Hook 2: another relevant icebreaker"
  ],
  "company_summary": "2-sentence summary for context"
}}

Return ONLY valid JSON."""

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(text)
        except Exception:
            return {
                "company_name": domain.split(".")[0].title(),
                "industry": "Unknown",
                "personalization_hooks": [f"I came across {domain} and was impressed by what you're building."],
                "company_summary": f"Company operating at {domain}",
                "tech_stack": [],
                "recent_news": [],
                "pain_points_likely": [],
            }

    @staticmethod
    async def research_lead(lead_id: str) -> dict:
        """Research a specific lead — company + role intel for personalization."""
        db = get_db()
        lead = await db.leads.find_one({"_id": lead_id})
        if not lead:
            return {"error": "Lead not found"}

        domain = lead.get("domain", "")
        if not domain and lead.get("email"):
            domain = lead["email"].split("@")[-1]

        company_research = {}
        if domain:
            company_research = await ResearchAgent.research_company(domain)

        model = _get_model()
        title = lead.get("title", "")
        company = lead.get("company", "")
        first_name = lead.get("first_name", "")

        prompt = f"""Generate personalized outreach intel for this lead.

Lead:
- Name: {first_name} {lead.get('last_name', '')}
- Title: {title}
- Company: {company}
- Domain: {domain}

Company intel already gathered:
{json.dumps(company_research, indent=2)[:2000]}

Return a JSON object:
{{
  "role_insights": "What this role likely cares about and their typical challenges",
  "personalized_hooks": [
    "Very specific personalized opening line for this person",
    "Alternative opening line"
  ],
  "talking_points": ["Key talking point relevant to their role", "Another talking point"],
  "avoid_topics": ["Things to avoid mentioning to this role"],
  "best_cta": "The most effective call-to-action for this role"
}}

Return ONLY valid JSON."""

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            lead_intel = json.loads(text)
        except Exception:
            lead_intel = {
                "role_insights": f"Decision maker at {company}",
                "personalized_hooks": [f"Hi {first_name}, I came across {company} and thought our solution could help your team."],
                "talking_points": [],
                "avoid_topics": [],
                "best_cta": "schedule a quick call",
            }

        # Merge and store research on the lead record
        research_data = {**company_research, **lead_intel, "researched_at": datetime.utcnow().isoformat()}
        await db.leads.update_one(
            {"_id": lead_id},
            {"$set": {"research_data": research_data, "updated_at": datetime.utcnow()}}
        )

        return research_data

    @staticmethod
    async def research_all_leads(campaign_id: str) -> dict:
        """Batch-research all unresearched leads in a campaign."""
        db = get_db()
        leads = await db.leads.find({
            "campaign_id": campaign_id,
            "is_suppressed": False,
            "research_data": {"$exists": False},
        }).to_list(50)  # Process up to 50 at a time

        researched = 0
        failed = 0
        for lead in leads:
            try:
                await ResearchAgent.research_lead(lead["_id"])
                researched += 1
            except Exception:
                failed += 1

        await db.agent_logs.insert_one(_log(
            ResearchAgent.NAME, campaign_id, "batch_research",
            f"Researched {researched} leads, {failed} failed, {len(leads)} total processed"
        ))

        return {
            "researched": researched,
            "failed": failed,
            "total_processed": len(leads),
            "campaign_id": campaign_id,
        }

    @staticmethod
    async def generate_hooks_for_lead(lead_id: str) -> list:
        """Return personalization hooks for a lead (research first if needed)."""
        db = get_db()
        lead = await db.leads.find_one({"_id": lead_id})
        if not lead:
            return []

        if not lead.get("research_data"):
            data = await ResearchAgent.research_lead(lead_id)
        else:
            data = lead["research_data"]

        hooks = data.get("personalized_hooks", []) or data.get("personalization_hooks", [])
        return hooks


# ========================================================================
#  6. LEAD IDENTIFICATION AGENT — Finds & ranks key decision-makers
# ========================================================================
class LeadIdentificationAgent:
    """
    Identifies and ranks the best leads (Key Persons) to contact:
    - Scores every lead against the campaign ICP (0-100)
    - Finds the top KDM at each target company
    - Deduplicates and surfaces highest-value contacts
    - Flags weak leads for drop/replacement
    """
    NAME = "kp_agent"

    @staticmethod
    async def score_and_rank_leads(campaign_id: str) -> dict:
        """Score ALL leads in a campaign and sort by ICP fit."""
        db = get_db()
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not campaign:
            return {"error": "Campaign not found"}

        icp = campaign.get("ideal_customer_profile", {})
        roles = campaign.get("roles", [])
        industries = campaign.get("industries", [])
        leads = await db.leads.find({
            "campaign_id": campaign_id,
            "is_suppressed": False,
        }).to_list(500)

        if not leads:
            return {"scored": 0, "top_leads": [], "weak_leads": []}

        model = _get_model()
        scored = []
        for lead in leads:
            # AI-powered ICP scoring
            prompt = f"""Score this lead's fit for the ICP on a scale of 0-100.

Lead:
- Title: {lead.get('title', '')}
- Company: {lead.get('company', '')}
- Domain: {lead.get('domain', '')}
- Seniority: {lead.get('seniority', '')}
- Department: {lead.get('department', '')}

ICP:
- Target roles: {roles}
- Target industries: {industries}
- Profile: {json.dumps(icp)}

Score criteria:
- 90-100: Perfect title + industry match, senior decision-maker
- 70-89: Good title or industry match
- 50-69: Partial match, could work
- 30-49: Weak match
- 0-29: Poor fit

Return ONLY a JSON: {{"score": <number>, "reason": "<one line reason>", "is_decision_maker": <true/false>}}"""

            try:
                resp = model.generate_content(prompt)
                text = resp.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                result = json.loads(text)
                score = float(result.get("score", 50))
                reason = result.get("reason", "")
                is_dm = result.get("is_decision_maker", False)
            except Exception:
                score = lead.get("profile_score", 50.0)
                reason = "Default score"
                is_dm = False

            # Update score in DB
            await db.leads.update_one(
                {"_id": lead["_id"]},
                {"$set": {
                    "profile_score": score,
                    "score_reason": reason,
                    "is_decision_maker": is_dm,
                    "updated_at": datetime.utcnow(),
                }}
            )
            scored.append({
                "id": lead["_id"],
                "name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip(),
                "title": lead.get("title", ""),
                "company": lead.get("company", ""),
                "email": lead.get("email", ""),
                "score": score,
                "reason": reason,
                "is_decision_maker": is_dm,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        top_leads = [l for l in scored if l["score"] >= 60]
        weak_leads = [l for l in scored if l["score"] < 40]

        await db.agent_logs.insert_one(_log(
            LeadIdentificationAgent.NAME, campaign_id, "score_and_rank",
            f"Scored {len(scored)} leads — {len(top_leads)} top, {len(weak_leads)} weak"
        ))

        return {
            "scored": len(scored),
            "top_leads": top_leads[:20],
            "weak_leads": weak_leads[:10],
            "average_score": round(sum(l["score"] for l in scored) / len(scored), 1) if scored else 0,
        }

    @staticmethod
    async def find_best_contact(campaign_id: str, domain: str) -> dict:
        """Find the single best KDM to contact at a company domain."""
        db = get_db()
        leads = await db.leads.find({
            "campaign_id": campaign_id,
            "domain": domain,
            "is_suppressed": False,
        }).to_list(50)

        if not leads:
            return {"error": f"No leads found for domain: {domain}"}

        # Pick highest-scored lead, or the one closest to decision-maker
        best = max(leads, key=lambda l: l.get("profile_score", 0))
        from models import doc_to_dict
        return {
            "best_contact": doc_to_dict(best),
            "total_contacts_at_domain": len(leads),
            "selection_reason": f"Highest ICP score ({best.get('profile_score', 0):.0f}/100)",
        }

    @staticmethod
    async def identify_key_persons(campaign_id: str) -> dict:
        """Identify and surface the best KDM from every target company."""
        db = get_db()
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not campaign:
            return {"error": "Campaign not found"}

        leads = await db.leads.find({
            "campaign_id": campaign_id,
            "is_suppressed": False,
        }).to_list(500)

        # Group by domain
        by_domain: dict[str, list] = {}
        for lead in leads:
            d = lead.get("domain", "unknown")
            by_domain.setdefault(d, []).append(lead)

        key_persons = []
        for domain, domain_leads in by_domain.items():
            best = max(domain_leads, key=lambda l: l.get("profile_score", 0))
            key_persons.append({
                "domain": domain,
                "company": best.get("company", domain),
                "key_person": {
                    "id": best["_id"],
                    "name": f"{best.get('first_name', '')} {best.get('last_name', '')}".strip(),
                    "title": best.get("title", ""),
                    "email": best.get("email", ""),
                    "score": best.get("profile_score", 0),
                    "is_decision_maker": best.get("is_decision_maker", False),
                },
                "total_contacts": len(domain_leads),
            })

        key_persons.sort(key=lambda x: x["key_person"]["score"], reverse=True)

        await db.agent_logs.insert_one(_log(
            LeadIdentificationAgent.NAME, campaign_id, "identify_key_persons",
            f"Identified {len(key_persons)} key persons across {len(by_domain)} companies"
        ))

        return {
            "total_companies": len(by_domain),
            "key_persons": key_persons,
            "decision_makers": [kp for kp in key_persons if kp["key_person"]["is_decision_maker"]],
        }

    @staticmethod
    async def flag_weak_leads(campaign_id: str, threshold: float = 30.0) -> dict:
        """Flag leads below the score threshold as low-priority."""
        db = get_db()
        result = await db.leads.update_many(
            {
                "campaign_id": campaign_id,
                "profile_score": {"$lt": threshold},
                "status": "raw",
            },
            {"$set": {"drop_reason": "low_icp_score", "updated_at": datetime.utcnow()}}
        )

        await db.agent_logs.insert_one(_log(
            LeadIdentificationAgent.NAME, campaign_id, "flag_weak_leads",
            f"Flagged {result.modified_count} leads with score < {threshold}"
        ))

        return {"flagged": result.modified_count, "threshold": threshold}


# ========================================================================
#  7. PERSONALIZATION AGENT — Creates hyper-personalized emails
# ========================================================================
class PersonalizationAgent:
    """
    Generates hyper-personalized outreach emails for each lead:
    - Pulls research data from ResearchAgent
    - Creates unique opening lines per lead
    - Batch-personalizes all pending outreach steps
    - Previews personalization before sending
    """
    NAME = "personalization_agent"

    @staticmethod
    async def generate_opening_line(lead_id: str, campaign_id: str) -> str:
        """Generate a unique AI-crafted personalized opening line for one lead."""
        db = get_db()
        lead = await db.leads.find_one({"_id": lead_id})
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not lead or not campaign:
            return ""

        research = lead.get("research_data", {})
        hooks = research.get("personalized_hooks") or research.get("personalization_hooks", [])
        hook_text = hooks[0] if hooks else ""

        model = _get_model()
        prompt = f"""Write a single personalized opening line for a cold sales email.

Lead: {lead.get('first_name', '')} {lead.get('last_name', '')}, {lead.get('title', '')} at {lead.get('company', '')}
Product: {campaign.get('product_name', '')} — {campaign.get('product_summary', '')}
Research hook: {hook_text}
Company intel: {json.dumps(research.get('recent_news', []))}

Rules:
- One sentence only
- Reference something specific about their company or role
- Natural, not salesy
- Don't start with "I" or "We"
- No emojis

Return ONLY the opening line text."""

        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return hook_text or f"I came across {lead.get('company', 'your company')} and thought this could be relevant."

    @staticmethod
    async def personalize_step(step_id: str) -> dict:
        """Re-personalize a single outreach step with research-backed content."""
        db = get_db()
        step = await db.outreach_steps.find_one({"_id": step_id})
        if not step:
            return {"error": "Step not found"}

        lead = await db.leads.find_one({"_id": step["lead_id"]})
        if not lead:
            return {"error": "Lead not found"}

        # Find campaign via lead
        campaign = await db.campaigns.find_one({"_id": lead.get("campaign_id", "")})
        if not campaign:
            return {"error": "Campaign not found"}

        # Generate a personalized opening line from research
        opening = await PersonalizationAgent.generate_opening_line(lead["_id"], campaign["_id"])

        # Prepend personalized opening to existing body
        existing_body = step.get("body", "")
        if opening and existing_body:
            # Insert the opening line as the first paragraph
            lines = existing_body.split("\n\n", 1)
            if len(lines) > 1:
                new_body = f"{opening}\n\n{lines[1]}"
            else:
                new_body = f"{opening}\n\n{existing_body}"
        else:
            new_body = existing_body

        await db.outreach_steps.update_one(
            {"_id": step_id},
            {"$set": {
                "body": new_body,
                "personalized_opening": opening,
                "is_personalized": True,
                "updated_at": datetime.utcnow(),
            }}
        )

        return {"step_id": step_id, "opening_line": opening, "updated_body": new_body}

    @staticmethod
    async def batch_personalize(campaign_id: str) -> dict:
        """Personalize all pending step 1 emails in a campaign using research data."""
        db = get_db()
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id, "is_suppressed": False}, {"_id": 1}
        )]

        if not lead_ids:
            return {"personalized": 0, "skipped": 0, "failed": 0}

        # Get first-step pending/approved emails only
        steps = await db.outreach_steps.find({
            "lead_id": {"$in": lead_ids},
            "step_number": 0,
            "step_type": "email",
            "is_personalized": {"$ne": True},
            "status": {"$in": ["pending", "approved"]},
        }).to_list(200)

        personalized = 0
        skipped = 0
        failed = 0

        for step in steps:
            lead = await db.leads.find_one({"_id": step["lead_id"]})
            if not lead:
                skipped += 1
                continue

            # Research first if not done
            if not lead.get("research_data"):
                try:
                    await ResearchAgent.research_lead(lead["_id"])
                except Exception:
                    skipped += 1
                    continue

            try:
                await PersonalizationAgent.personalize_step(step["_id"])
                personalized += 1
            except Exception:
                failed += 1

        await db.agent_logs.insert_one(_log(
            PersonalizationAgent.NAME, campaign_id, "batch_personalize",
            f"Personalized {personalized} emails, {skipped} skipped, {failed} failed"
        ))

        return {"personalized": personalized, "skipped": skipped, "failed": failed}

    @staticmethod
    async def preview_personalization(lead_id: str, campaign_id: str) -> dict:
        """Preview what a personalized email would look like for a lead."""
        db = get_db()
        lead = await db.leads.find_one({"_id": lead_id})
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not lead or not campaign:
            return {"error": "Lead or campaign not found"}

        # Get research (or generate on the fly)
        if not lead.get("research_data"):
            research = await ResearchAgent.research_lead(lead_id)
        else:
            research = lead["research_data"]

        opening = await PersonalizationAgent.generate_opening_line(lead_id, campaign_id)
        hooks = research.get("personalized_hooks", []) or research.get("personalization_hooks", [])
        talking_points = research.get("talking_points", [])

        from models import doc_to_dict
        return {
            "lead": doc_to_dict(lead),
            "opening_line": opening,
            "hooks": hooks,
            "talking_points": talking_points,
            "role_insights": research.get("role_insights", ""),
            "best_cta": research.get("best_cta", "schedule a quick call"),
            "company_summary": research.get("company_summary", ""),
            "recent_news": research.get("recent_news", []),
        }


# ========================================================================
#  8. OUTREACH AGENT — Orchestrates the full send pipeline
# ========================================================================
class OutreachAgent:
    """
    Full outreach pipeline orchestration:
    - Approves and sends emails in batch
    - Manages the send queue with priority ordering
    - Enforces rate limits and send windows
    - Tracks delivery and advances sequences automatically
    """
    NAME = "outreach_agent"

    @staticmethod
    async def get_send_queue(campaign_id: str) -> dict:
        """Get prioritized send queue — approved steps ready to send."""
        db = get_db()
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id, "is_suppressed": False}, {"_id": 1}
        )]

        steps = await db.outreach_steps.find({
            "lead_id": {"$in": lead_ids},
            "status": {"$in": ["pending", "approved"]},
            "step_type": "email",
        }).sort("step_number", 1).to_list(500)

        leads_map = {l["_id"]: l async for l in db.leads.find(
            {"_id": {"$in": list({s["lead_id"] for s in steps})}},
        )}

        queue = []
        for step in steps:
            lead = leads_map.get(step["lead_id"], {})
            from models import doc_to_dict
            queue.append({
                "step": doc_to_dict(step),
                "lead_name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip(),
                "lead_email": lead.get("email", ""),
                "company": lead.get("company", ""),
                "profile_score": lead.get("profile_score", 0),
                "priority": "high" if lead.get("profile_score", 0) >= 70 else "normal",
            })

        # Sort: high-priority + approved first
        queue.sort(key=lambda x: (
            0 if x["step"].get("status") == "approved" else 1,
            0 if x["priority"] == "high" else 1,
            -x["profile_score"],
        ))

        return {
            "total_queued": len(queue),
            "approved": len([q for q in queue if q["step"]["status"] == "approved"]),
            "pending_approval": len([q for q in queue if q["step"]["status"] == "pending"]),
            "high_priority": len([q for q in queue if q["priority"] == "high"]),
            "queue": queue[:50],
        }

    @staticmethod
    async def batch_approve_and_send(campaign_id: str, only_high_priority: bool = False) -> dict:
        """Approve all pending steps and send all approved steps."""
        from services.email_sender import send_step as send_step_email
        db = get_db()

        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id, "is_suppressed": False}, {"_id": 1}
        )]

        # Optionally filter to high-priority leads only
        filter_q: dict = {"lead_id": {"$in": lead_ids}, "step_type": "email"}
        if only_high_priority:
            high_ids = [l["_id"] async for l in db.leads.find(
                {"campaign_id": campaign_id, "is_suppressed": False, "profile_score": {"$gte": 70}},
                {"_id": 1}
            )]
            filter_q["lead_id"] = {"$in": high_ids}

        # 1. Auto-approve all pending step-0 (first contact) emails
        await db.outreach_steps.update_many(
            {**filter_q, "status": "pending", "step_number": 0},
            {"$set": {"status": "approved", "approved": True, "updated_at": datetime.utcnow()}}
        )

        # 2. Send all approved emails
        approved_steps = await db.outreach_steps.find(
            {**filter_q, "status": "approved"}
        ).to_list(500)

        sent_ok = 0
        sent_fail = 0
        errors = []

        for step in approved_steps:
            result = await send_step_email(step["_id"])
            if "error" in result:
                sent_fail += 1
                errors.append(result["error"])
            else:
                sent_ok += 1

        await db.agent_logs.insert_one(_log(
            OutreachAgent.NAME, campaign_id, "batch_approve_and_send",
            f"Sent {sent_ok}, failed {sent_fail}, high_priority_only={only_high_priority}"
        ))

        return {
            "sent": sent_ok,
            "failed": sent_fail,
            "errors": errors[:5],
            "high_priority_only": only_high_priority,
        }

    @staticmethod
    async def run_full_pipeline(campaign_id: str) -> dict:
        """
        Run the complete outreach pipeline end-to-end:
        1. Score & rank leads
        2. Research unresearched leads
        3. Personalize pending emails
        4. Advance no-reply leads
        5. Send all approved emails
        """
        results = {}

        # Step 1: Score leads
        score_result = await LeadIdentificationAgent.score_and_rank_leads(campaign_id)
        results["scoring"] = {"top": len(score_result.get("top_leads", [])),
                               "weak": len(score_result.get("weak_leads", []))}

        # Step 2: Research leads
        research_result = await ResearchAgent.research_all_leads(campaign_id)
        results["research"] = research_result

        # Step 3: Personalize emails
        pers_result = await PersonalizationAgent.batch_personalize(campaign_id)
        results["personalization"] = pers_result

        # Step 4: Advance no-reply leads
        advance_result = await MailAgent.auto_send_next(campaign_id)
        results["sequence_advance"] = advance_result

        # Step 5: Send approved emails
        send_result = await OutreachAgent.batch_approve_and_send(campaign_id)
        results["send"] = send_result

        db = get_db()
        await db.agent_logs.insert_one(_log(
            OutreachAgent.NAME, campaign_id, "full_pipeline_run",
            f"Pipeline complete — scored, researched, personalized, advanced, sent"
        ))

        return results

    @staticmethod
    async def get_outreach_stats(campaign_id: str) -> dict:
        """Get real-time outreach stats."""
        db = get_db()
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id}, {"_id": 1}
        )]

        pipeline = [
            {"$match": {"lead_id": {"$in": lead_ids}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        status_counts = {}
        async for doc in db.outreach_steps.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]

        sent = status_counts.get("sent", 0)
        replies = await db.replies.count_documents({"lead_id": {"$in": lead_ids}})

        return {
            "total_leads": len(lead_ids),
            "pending": status_counts.get("pending", 0),
            "approved": status_counts.get("approved", 0),
            "sent": sent,
            "reply_rate": round((replies / sent * 100) if sent > 0 else 0, 1),
            "replies": replies,
        }


# ========================================================================
#  9. RESPONSE HANDLING AGENT — Enhanced reply handling with auto-send
# ========================================================================
class ResponseHandlingAgent:
    """
    Enhanced incoming reply handler:
    - Wraps ReplyAgent with auto-send capability
    - Processes all unhandled replies in bulk
    - Tracks response queue with priority triage
    - Auto-sends replies for low-risk intents (out_of_office, unsubscribe)
    """
    NAME = "response_handling_agent"

    @staticmethod
    async def get_response_queue(campaign_id: str) -> dict:
        """Get all unhandled replies with triage priority."""
        db = get_db()
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id}, {"_id": 1}
        )]

        replies = await db.replies.find({
            "lead_id": {"$in": lead_ids},
            "is_handled": False,
        }).sort("received_at", -1).to_list(200)

        # Enrich with lead info
        leads_map = {}
        async for lead in db.leads.find({"_id": {"$in": [r["lead_id"] for r in replies]}}):
            leads_map[lead["_id"]] = lead

        queue = []
        from models import doc_to_dict
        for reply in replies:
            lead = leads_map.get(reply["lead_id"], {})
            intent = reply.get("intent", "unknown")
            priority = (
                "urgent" if intent in ("schedule_call", "demo_request", "interested", "pricing")
                else "normal" if intent in ("question", "objection", "referral")
                else "low"
            )
            queue.append({
                "reply": doc_to_dict(reply),
                "lead_name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip(),
                "company": lead.get("company", ""),
                "intent": intent,
                "priority": priority,
                "has_draft": bool(reply.get("ai_draft_reply")),
            })

        # Sort by priority
        priority_order = {"urgent": 0, "normal": 1, "low": 2}
        queue.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return {
            "total_unhandled": len(queue),
            "urgent": len([q for q in queue if q["priority"] == "urgent"]),
            "normal": len([q for q in queue if q["priority"] == "normal"]),
            "low_priority": len([q for q in queue if q["priority"] == "low"]),
            "queue": queue[:30],
        }

    @staticmethod
    async def auto_respond(reply_id: str) -> dict:
        """Auto-send the AI-generated draft response for a reply."""
        from services.email_sender import send_email
        db = get_db()
        reply = await db.replies.find_one({"_id": reply_id})
        if not reply:
            return {"error": "Reply not found"}

        draft = reply.get("ai_draft_reply", "")
        if not draft:
            return {"error": "No draft response available"}

        lead = await db.leads.find_one({"_id": reply["lead_id"]})
        if not lead:
            return {"error": "Lead not found"}

        campaign = await db.campaigns.find_one({"_id": lead.get("campaign_id", "")})
        if not campaign:
            return {"error": "Campaign not found"}

        # Send the auto-reply (convert plain text to simple HTML)
        subject = f"Re: {reply.get('subject', '')}"
        html_draft = draft.replace("\n\n", "<br><br>").replace("\n", "<br>")
        try:
            result = await send_email(
                to_email=reply.get("from_email", lead["email"]),
                subject=subject,
                html_body=html_draft,
                from_name=campaign.get("sender_name", ""),
                from_email=campaign.get("sender_email", ""),
            )
            if "error" in result:
                return result
            # Mark reply as handled
            await db.replies.update_one(
                {"_id": reply_id},
                {"$set": {"is_handled": True, "auto_responded": True, "handled_at": datetime.utcnow()}}
            )
            await db.agent_logs.insert_one(_log(
                ResponseHandlingAgent.NAME, lead.get("campaign_id", ""), "auto_respond",
                f"Auto-sent reply to {lead.get('email', '')} — intent: {reply.get('intent', '')}"
            ))
            return {"success": True, "sent_to": lead.get("email", ""), "intent": reply.get("intent", "")}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def handle_all_unhandled(campaign_id: str, auto_send_low_risk: bool = False) -> dict:
        """Process all unhandled replies — generate drafts and optionally auto-send low-risk ones."""
        db = get_db()
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id}, {"_id": 1}
        )]

        unhandled = await db.replies.find({
            "lead_id": {"$in": lead_ids},
            "is_handled": False,
            "ai_draft_reply": "",
        }).to_list(100)

        processed = 0
        auto_sent = 0
        failed = 0
        low_risk_intents = {"out_of_office", "unsubscribe", "not_interested"}

        for reply in unhandled:
            lead = await db.leads.find_one({"_id": reply["lead_id"]})
            campaign = await db.campaigns.find_one({"_id": lead.get("campaign_id", "")}) if lead else None
            if not lead or not campaign:
                continue

            try:
                intent_data = await ReplyAgent.classify_intent(reply.get("body", ""))
                response_data = await ReplyAgent.generate_response(
                    reply.get("body", ""), intent_data, campaign, lead
                )

                await db.replies.update_one(
                    {"_id": reply["_id"]},
                    {"$set": {
                        "intent": intent_data.get("intent", "question"),
                        "intent_data": intent_data,
                        "ai_draft_reply": response_data["reply_text"],
                        "updated_at": datetime.utcnow(),
                    }}
                )
                processed += 1

                # Auto-send for low-risk intents if enabled
                if auto_send_low_risk and intent_data.get("intent") in low_risk_intents:
                    send_result = await ResponseHandlingAgent.auto_respond(reply["_id"])
                    if send_result.get("success"):
                        auto_sent += 1

            except Exception:
                failed += 1

        await db.agent_logs.insert_one(_log(
            ResponseHandlingAgent.NAME, campaign_id, "handle_all_unhandled",
            f"Processed {processed} replies, auto-sent {auto_sent}, failed {failed}"
        ))

        return {
            "processed": processed,
            "auto_sent": auto_sent,
            "failed": failed,
            "total_unhandled": len(unhandled),
        }


# ========================================================================
#  10. BOOKING AGENT — Converts interested leads into booked meetings
# ========================================================================
class BookingAgent:
    """
    Converts hot leads into booked meetings:
    - Surfaces leads showing booking intent (schedule_call, demo_request, interested)
    - Sends personalized booking links to hot leads
    - Follows up with leads who expressed interest but haven't booked
    - Tracks the full booking pipeline
    """
    NAME = "booking_agent"

    @staticmethod
    async def get_hot_leads(campaign_id: str) -> dict:
        """Get all leads showing strong buying / booking signals."""
        db = get_db()
        # Leads who replied with high-intent
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id}, {"_id": 1}
        )]

        hot_intents = {"schedule_call", "demo_request", "interested", "pricing"}

        hot_replies = await db.replies.find({
            "lead_id": {"$in": lead_ids},
            "intent": {"$in": list(hot_intents)},
        }).sort("received_at", -1).to_list(100)

        # Also surface converted leads
        converted_leads = await db.leads.find({
            "campaign_id": campaign_id,
            "status": "converted",
        }).to_list(100)
        converted_ids = {l["_id"] for l in converted_leads}

        # Enrich with lead data
        leads_map = {}
        async for lead in db.leads.find({"_id": {"$in": [r["lead_id"] for r in hot_replies]}}):
            leads_map[lead["_id"]] = lead

        campaign = await db.campaigns.find_one({"_id": campaign_id})
        booking_link = (campaign or {}).get("calendly_url") or (campaign or {}).get("demo_booking_url", "")

        hot_list = []
        from models import doc_to_dict
        seen_ids = set()
        for reply in hot_replies:
            lead_id = reply["lead_id"]
            if lead_id in seen_ids:
                continue
            seen_ids.add(lead_id)
            lead = leads_map.get(lead_id, {})
            hot_list.append({
                "lead": doc_to_dict(lead) if lead else {"id": lead_id},
                "intent": reply.get("intent", ""),
                "reply_body": reply.get("body", "")[:200],
                "received_at": reply.get("received_at", "").isoformat() if hasattr(reply.get("received_at"), "isoformat") else str(reply.get("received_at", "")),
                "is_booked": lead.get("is_booked", False) if lead else False,
                "already_converted": lead_id in converted_ids,
                "booking_link": booking_link,
            })

        return {
            "hot_leads": hot_list,
            "total_hot": len(hot_list),
            "booked": len([h for h in hot_list if h["is_booked"]]),
            "pending_booking": len([h for h in hot_list if not h["is_booked"]]),
            "booking_link": booking_link,
        }

    @staticmethod
    async def send_booking_link(lead_id: str, campaign_id: str, custom_message: str = "") -> dict:
        """Send a booking/Calendly link to an interested lead."""
        from services.email_sender import send_email
        db = get_db()
        lead = await db.leads.find_one({"_id": lead_id})
        campaign = await db.campaigns.find_one({"_id": campaign_id})
        if not lead or not campaign:
            return {"error": "Lead or campaign not found"}

        booking_link = campaign.get("calendly_url") or campaign.get("demo_booking_url", "")
        if not booking_link:
            return {"error": "No booking link configured. Add a Calendly URL to your campaign."}

        first_name = lead.get("first_name", "there")
        sender_name = campaign.get("sender_name", "The Team")
        product_name = campaign.get("product_name", "")

        if custom_message:
            body = custom_message
        else:
            model = _get_model()
            prompt = f"""Write a short 3-4 sentence email to follow up and share a meeting booking link.

Lead: {first_name} {lead.get('last_name', '')}, {lead.get('title', '')} at {lead.get('company', '')}
Product: {product_name}
Sender: {sender_name}
Booking link: {booking_link}

Instructions:
- Warm, personal tone
- Reference their interest/reply
- Clearly share the booking link
- One clear CTA to book a time
- Sign off from {sender_name}

Return ONLY the email body text."""
            try:
                resp = model.generate_content(prompt)
                body = resp.text.strip()
            except Exception:
                body = f"Hi {first_name},\n\nThank you for your interest in {product_name}! I'd love to find a time to connect.\n\nFeel free to grab a slot that works best for you: {booking_link}\n\nLooking forward to speaking with you!\n\nBest,\n{sender_name}"

        subject = f"Let's connect — book a time with {sender_name}"
        html_body = body.replace("\n\n", "<br><br>").replace("\n", "<br>")
        try:
            result = await send_email(
                to_email=lead["email"],
                subject=subject,
                html_body=html_body,
                from_name=campaign.get("sender_name", ""),
                from_email=campaign.get("sender_email", ""),
            )
            if "error" in result:
                return result

            # Mark lead as booking link sent
            await db.leads.update_one(
                {"_id": lead_id},
                {"$set": {"booking_link_sent": True, "updated_at": datetime.utcnow()}}
            )

            await db.agent_logs.insert_one(_log(
                BookingAgent.NAME, campaign_id, "send_booking_link",
                f"Sent booking link to {lead.get('email', '')} — {first_name} at {lead.get('company', '')}"
            ))

            return {
                "success": True,
                "sent_to": lead["email"],
                "booking_link": booking_link,
                "message_sent": body,
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def confirm_booking(lead_id: str, campaign_id: str, meeting_info: dict = None) -> dict:
        """Mark a lead as booked and log the meeting."""
        db = get_db()
        update_data = {
            "is_booked": True,
            "status": "converted",
            "updated_at": datetime.utcnow(),
        }
        if meeting_info:
            update_data["meeting_info"] = meeting_info

        await db.leads.update_one({"_id": lead_id}, {"$set": update_data})

        lead = await db.leads.find_one({"_id": lead_id})
        await db.agent_logs.insert_one(_log(
            BookingAgent.NAME, campaign_id, "booking_confirmed",
            f"Meeting booked with {lead.get('first_name', '')} {lead.get('last_name', '')} at {lead.get('company', '')}"
        ))

        return {"success": True, "lead_id": lead_id, "status": "converted"}

    @staticmethod
    async def follow_up_unbooked(campaign_id: str) -> dict:
        """Follow up with hot leads who haven't booked yet."""
        db = get_db()
        lead_ids = [l["_id"] async for l in db.leads.find(
            {"campaign_id": campaign_id}, {"_id": 1}
        )]

        # Leads who replied with interest but haven't booked
        hot_replies = await db.replies.find({
            "lead_id": {"$in": lead_ids},
            "intent": {"$in": ["schedule_call", "demo_request", "interested"]},
        }).to_list(100)

        followed_up = 0
        skipped = 0
        for reply in hot_replies:
            lead = await db.leads.find_one({"_id": reply["lead_id"]})
            if not lead or lead.get("is_booked") or lead.get("booking_link_sent"):
                skipped += 1
                continue

            # Check if 48+ hours since reply with no booking
            received = reply.get("received_at", datetime.utcnow())
            if (datetime.utcnow() - received).total_seconds() < 48 * 3600:
                skipped += 1
                continue

            result = await BookingAgent.send_booking_link(lead["_id"], campaign_id)
            if result.get("success"):
                followed_up += 1
            else:
                skipped += 1

        await db.agent_logs.insert_one(_log(
            BookingAgent.NAME, campaign_id, "follow_up_unbooked",
            f"Followed up with {followed_up} unbooked hot leads, {skipped} skipped"
        ))

        return {"followed_up": followed_up, "skipped": skipped}

    @staticmethod
    async def get_booking_pipeline(campaign_id: str) -> dict:
        """Get full booking funnel stats."""
        db = get_db()
        total_leads = await db.leads.count_documents({"campaign_id": campaign_id})
        contacted = await db.leads.count_documents({
            "campaign_id": campaign_id,
            "status": {"$in": ["contacted", "replied", "converted"]},
        })
        replied = await db.leads.count_documents({"campaign_id": campaign_id, "status": "replied"})
        converted = await db.leads.count_documents({"campaign_id": campaign_id, "status": "converted"})
        booked = await db.leads.count_documents({"campaign_id": campaign_id, "is_booked": True})

        lead_ids = [l["_id"] async for l in db.leads.find({"campaign_id": campaign_id}, {"_id": 1})]
        hot_reply_count = await db.replies.count_documents({
            "lead_id": {"$in": lead_ids},
            "intent": {"$in": ["schedule_call", "demo_request", "interested", "pricing"]},
        })

        return {
            "funnel": {
                "total_leads": total_leads,
                "contacted": contacted,
                "replied": replied,
                "interested": hot_reply_count,
                "converted": converted,
                "booked": booked,
            },
            "conversion_rate": round((converted / total_leads * 100) if total_leads else 0, 1),
            "booking_rate": round((booked / total_leads * 100) if total_leads else 0, 1),
        }
