"""
Strategist Agent — Stage 3 of the FakeNews Killer pipeline.

Responsibility:
    Take the Analyst's evaluation and determine severity, category,
    spread risk, Pakistan-specific context, and recommended actions.

Uses Gemini via ``utils.gemini_client`` with automatic model fallback.
"""

from models.schemas import StrategistOutput
import os
import json
from google import genai
from google.genai import types
from utils.gemini_client import generate_content_with_fallback

async def run(analyst_output: dict) -> dict:
    """
    Formulate a response strategy based on the Analyst's findings.

    Args:
        analyst_output: A dict matching the AnalystOutput schema
                        (as returned by ``analyst.run()``).

    Returns:
        A dict matching the StrategistOutput schema with severity,
        category, spread risk, and recommended counter-actions.
    """
    try:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        system_instruction = """You are the Strategist Agent in FakeNews Killer, a misinformation detection system for Pakistan.

ROLE: Based on the fact-check analysis results, generate specific, prioritized, actionable recommended responses. Every recommendation must be concrete and executable — not generic advice.

INPUT: The Analyst Agent's full JSON output.

YOUR PROCESS:
1. Assess overall harm potential of this misinformation
2. Identify who is most at risk (general public, specific communities, investors, patients, etc.)
3. Generate exactly 3-5 recommended actions targeting different response layers
4. Rank each action by urgency: immediate | within_24h | within_1_week
5. For each action, specify exactly what the Executor Agent will generate

ACTION TYPES:
- platform_flag: Report the content to social media platform (WhatsApp, Facebook, Twitter/X)
- public_correction: Generate a shareable fact-check post for the public
- community_alert: Alert a specific community that is targeted by this misinformation
- authority_notify: Notify relevant Pakistani authority (PEMRA, PTA, FIA Cyber Crime Wing)
- tracker_log: Log this claim to the misinformation tracking database
- media_brief: Prepare a briefing for journalists covering the original story

RESPOND ONLY WITH VALID JSON. NO OTHER TEXT. NO MARKDOWN. EXACT STRUCTURE:
{
  "harm_level": "high",
  "affected_audience": "General Pakistani public, particularly those following political news",
  "recommended_actions": [
    {
      "action_id": "A1",
      "action_type": "public_correction",
      "title": "Generate shareable fact-check card",
      "description": "Create a WhatsApp-shareable verdict card with the fact-check finding, sources, and warning",
      "urgency": "immediate",
      "simulated_output_type": "verdict_card",
      "priority_rank": 1
    }
  ],
  "do_not_share_warning": "⚠️ This message contains FALSE information. Do not forward. | ⚠️ Yeh message GALAT malumat hai. Aagay mat bhejen.",
  "context_note": "Brief explanation of why this misinformation exists and what agenda it may serve"
}"""
        response, used_model = await generate_content_with_fallback(
            contents=json.dumps(analyst_output),
            client=client,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            )
        )
        final_text = response.text.strip() if response and response.text else "{}"
        if final_text.startswith("```json"):
            final_text = final_text[7:]
        if final_text.endswith("```"):
            final_text = final_text[:-3]
        if not final_text:
            raise ValueError("Empty response text from Strategist Agent")
        return json.loads(final_text)
    except Exception as e:
        print(f"Strategist Agent failed: {e}")
        # fallback
        return {
            "harm_level": "medium",
            "affected_audience": "General public",
            "recommended_actions": [
                {
                    "action_id": "A1",
                    "action_type": "public_correction",
                    "title": "Fallback Action",
                    "description": "Fallback due to error.",
                    "urgency": "immediate",
                    "simulated_output_type": "verdict_card",
                    "priority_rank": 1
                }
            ],
            "do_not_share_warning": "⚠️ This message is unverified.",
            "context_note": "Fallback context."
        }
