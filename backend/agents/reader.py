"""
Reader Agent — Stage 1 of the FakeNews Killer pipeline.

Responsibility:
    Accept raw text input, clean it, detect the language,
    and extract individual factual claims for downstream analysis.

Uses Gemini via ``utils.gemini_client`` with automatic model fallback.
"""

from models.schemas import ReaderOutput
import os
import json
from google import genai
from google.genai import types
from utils.gemini_client import generate_content_with_fallback

async def run(text: str) -> dict:
    """
    Process raw user-submitted text and return structured claims.

    Args:
        text: The raw text / article / social-media post to analyse.

    Returns:
        A dict matching the ReaderOutput schema with extracted claims,
        detected language, and metadata.
    """
    try:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        system_instruction = """You are the Reader Agent in FakeNews Killer, a misinformation detection system for Pakistan.

ROLE: Extract every discrete, verifiable factual claim from raw user input. Input may be a WhatsApp forward, social media post, news screenshot (converted to text), or article — in English, Urdu, or Roman Urdu.

CRITICAL RULE: Do NOT summarize. Extract individual, independently checkable claims. "PM ne resign kar diya aur army ne control le lia" contains TWO claims — treat them separately.

YOUR PROCESS:
1. Detect language: english | urdu | roman_urdu | mixed
2. Identify content type: whatsapp_forward | news_article | social_post | screenshot
3. Scan for red-flag linguistic patterns: "SHARE IMMEDIATELY", "آگے بھیجیں", unnamed sources ("a reliable source said"), round numbers stated as exact facts, sensational ALL CAPS language, urgency phrases
4. Extract every discrete, verifiable claim — normalize each into a clean searchable English statement
5. Assign an initial suspicion score (0-10) based on linguistic red flags alone — before any fact-checking

RESPOND ONLY WITH VALID JSON. NO OTHER TEXT. NO MARKDOWN. EXACT STRUCTURE:
{
  "content_type": "whatsapp_forward",
  "language_detected": "roman_urdu",
  "red_flag_patterns": ["SHARE IMMEDIATELY", "unnamed source"],
  "initial_suspicion_score": 8,
  "claims": [
    {
      "claim_id": "C1",
      "original_text": "exact phrase from input",
      "normalized_claim": "clean searchable English statement of this claim",
      "claim_type": "event | statistic | quote | policy | image_description",
      "entities": ["named people, organizations, or places"],
      "time_reference": "today | yesterday | specific date | vague | none",
      "verifiable": true
    }
  ],
  "total_claims": 2
}"""
        response, used_model = await generate_content_with_fallback(
            contents=text,
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
            raise ValueError("Empty response text from Reader Agent")
        return json.loads(final_text)
    except Exception as e:
        print(f"Reader Agent failed: {e}")
        # fallback
        return {
            "content_type": "text",
            "language_detected": "en",
            "red_flag_patterns": [],
            "initial_suspicion_score": 5,
            "claims": [
                {
                    "claim_id": "C1",
                    "original_text": text,
                    "normalized_claim": text,
                    "claim_type": "event",
                    "entities": [],
                    "time_reference": "vague",
                    "verifiable": True
                }
            ],
            "total_claims": 1
        }
