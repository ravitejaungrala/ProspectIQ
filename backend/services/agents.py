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
