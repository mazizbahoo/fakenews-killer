"""
Executor Agent — Stage 4 (final) of the FakeNews Killer pipeline.

Responsibility:
    Compile outputs from all previous agents into a final verdict,
    write the result to the misinformation tracker (Firestore), and
    return a user-facing report.

Uses Gemini via ``utils.gemini_client`` with automatic model fallback.
"""

from models.schemas import ExecutorOutput
from models.database import insert_tracker_entry
import json
import os
from google import genai
from google.genai import types

from utils.gemini_client import generate_content_with_fallback

async def run(strategist_output: dict, analyst_output: dict, reader_output: dict = None) -> dict:
    """
    Produce the final verdict and persist it to the tracker database.

    Args:
        strategist_output: A dict matching the StrategistOutput schema
                           (as returned by ``strategist.run()``).
        analyst_output:    A dict matching the AnalystOutput schema
                           (needed for per-claim breakdown).
        reader_output:     A dict matching the ReaderOutput schema.

    Returns:
        A dict matching the ExecutorOutput schema with the overall
        verdict, confidence score, detailed analysis, and Urdu summary.
    """
    try:
        combined_input = {
            "reader_output": reader_output or {},
            "analyst_output": analyst_output,
            "strategist_output": strategist_output
        }
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        system_instruction = """You are the Executor Agent in FakeNews Killer, a misinformation detection system for Pakistan.

ROLE: Carry out the top 3 recommended actions. Generate all tangible outputs — verdict card data, tracker database entry, and platform report — complete and ready for real-world use.

INPUT: The combined output from ALL previous agents (Reader + Analyst + Strategist results as one JSON object).

YOU MUST ALWAYS EXECUTE EXACTLY THESE THREE ACTIONS. No exceptions.

ACTION 1 — VERDICT CARD
Generate complete structured data for a shareable visual fact-check card. This will be rendered as a UI component in the mobile app and shared via WhatsApp. Every field will be displayed — make them clear, accurate, and appropriately alarming or reassuring.

ACTION 2 — TRACKER LOG ENTRY
Generate a complete database insert object as if writing to the FakeNews Killer misinformation tracker. Include all metadata. Use the entry_id format: FNK-[YYYYMMDD]-[3 digit random number].

ACTION 3 — PLATFORM REPORT
Write a complete, professional content abuse report as if being formally submitted to a social media platform. Use formal, precise language. This should look like something a legal team would send.

RESPOND ONLY WITH VALID JSON. NO OTHER TEXT. NO MARKDOWN. EXACT STRUCTURE:
{
  "execution_timestamp": "2024-12-05T09:23:10Z",
  "actions_executed": 3,
  "verdict_card": {
    "claim_summary": "One sentence: what claim was checked",
    "overall_verdict": "FALSE",
    "verdict_color": "red",
    "confidence_percentage": 91,
    "key_finding": "One clear sentence stating the fact-check finding",
    "sources": ["Dawn", "Geo News"],
    "fact_checked_by": "FakeNews Killer AI",
    "check_timestamp": "December 5, 2024 at 9:23 AM",
    "share_text": "✅ Fact Checked by FakeNews Killer: [key finding]. Source: [source]. Visit fakenewskiller.app to check more.",
    "urdu_verdict": "جھوٹ",
    "roman_urdu_warning": "⚠️ Yeh khabar BILKUL GALAT hai. Aagay mat bhejen. FakeNews Killer ne verify kiya."
  },
  "tracker_entry": {
    "entry_id": "FNK-20241205-042",
    "claim_text": "normalized claim text",
    "verdict": "false",
    "category": "political | health | economic | religious | security | other",
    "language": "roman_urdu",
    "spread_risk": "high",
    "first_detected": "2024-12-05T09:23:10Z",
    "sources_cited": ["Dawn.com", "Geo.tv"],
    "tags": ["political", "election", "WhatsApp forward"],
    "status": "logged"
  },
  "platform_report": {
    "report_type": "Misinformation / False News",
    "platform": "WhatsApp",
    "content_description": "Description of the reported content",
    "harm_category": "Political Manipulation / Public Safety / Health Misinformation",
    "evidence_summary": "Summary of evidence found against this content",
    "recommended_action": "Remove content / Add fact-check label / Reduce algorithmic distribution",
    "reporter": "FakeNews Killer Automated Detection System — fakenewskiller.app",
    "report_body": "FORMAL REPORT BODY: Full professional text of the report, 3-4 paragraphs, suitable for submission to a platform's trust and safety team."
  },
  "execution_log": [
    {"step": 1, "action": "verdict_card_generated", "status": "success", "timestamp": "2024-12-05T09:23:09Z"},
    {"step": 2, "action": "tracker_entry_created", "entry_id": "FNK-20241205-042", "status": "success", "timestamp": "2024-12-05T09:23:09Z"},
    {"step": 3, "action": "platform_report_drafted", "platform": "WhatsApp", "status": "success", "timestamp": "2024-12-05T09:23:10Z"}
  ]
}"""
        response, used_model = await generate_content_with_fallback(
            contents=json.dumps(combined_input),
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
            final_text = "{}"
            
        result = json.loads(final_text)
        if not result:
            raise ValueError("Empty JSON object parsed")
        
        tracker_data = result.get("tracker_entry", {})
        verdict_card_data = result.get("verdict_card", {})
        confidence = verdict_card_data.get("confidence_percentage", 0)
        
        insert_tracker_entry(
            claim_text=tracker_data.get("claim_text", "Unknown claim"),
            verdict=tracker_data.get("verdict", "unverified"),
            category=tracker_data.get("category", "other"),
            language=tracker_data.get("language", "en"),
            spread_risk=tracker_data.get("spread_risk", "medium"),
            sources_cited=json.dumps(tracker_data.get("sources_cited", [])),
            tags=json.dumps(tracker_data.get("tags", [])),
            status=tracker_data.get("status", "logged"),
            confidence_score=confidence,
            analyst_data=analyst_output,
            executor_data=result,
        )
        
        return result
    except Exception as e:
        print(f"Executor Agent failed: {e}")
        # fallback
        return {
            "execution_timestamp": "2024-12-05T09:23:10Z",
            "actions_executed": 0,
            "verdict_card": {
                "claim_summary": "System currently experiencing high load.",
                "overall_verdict": "UNVERIFIED",
                "verdict_color": "grey",
                "confidence_percentage": 0,
                "key_finding": "We're sorry, but the AI verification system is currently over capacity (API Quota Exceeded). Please try again later.",
                "sources": [],
                "fact_checked_by": "FakeNews Killer AI",
                "check_timestamp": "N/A",
                "share_text": "System over capacity. Please try again later.",
                "urdu_verdict": "Unverified",
                "roman_urdu_warning": "Warning"
            },
            "tracker_entry": {
                "entry_id": "FNK-00000000-000",
                "claim_text": "System over capacity",
                "verdict": "unverified",
                "category": "other",
                "language": "en",
                "spread_risk": "medium",
                "first_detected": "2024-12-05T09:23:10Z",
                "sources_cited": [],
                "tags": [],
                "status": "logged"
            },
            "platform_report": {},
            "execution_log": []
        }
