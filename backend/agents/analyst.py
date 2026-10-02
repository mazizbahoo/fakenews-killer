"""
Analyst Agent — Stage 2 of the FakeNews Killer pipeline.

Responsibility:
    Receive the structured claims from the Reader and evaluate each
    claim for truthfulness, providing evidence and confidence scores.

Uses Gemini via ``utils.gemini_client`` with automatic model fallback.
"""

from models.schemas import AnalystOutput
import os
import json
from google import genai
from google.genai import types
from utils.gemini_client import generate_content_with_fallback

async def run(reader_output: dict) -> dict:
    """
    Analyse the claims extracted by the Reader agent.

    Args:
        reader_output: A dict matching the ReaderOutput schema
                       (as returned by ``reader.run()``).

    Returns:
        A dict matching the AnalystOutput schema with per-claim
        verdicts, evidence, and an overall credibility score.
    """
    try:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        system_instruction = """You are the Analyst Agent in FakeNews Killer, a misinformation detection system for Pakistan.

ROLE: Fact-check each extracted claim using web search. Assign a truth confidence score to every claim. Identify specifically WHY each claim is true, false, misleading, or unverifiable.

YOU HAVE ACCESS TO WEB SEARCH. Use it for every claim. Search aggressively.

PREFERRED SOURCES (in order of trust): Dawn, Geo News, ARY News, The News, Tribune, Reuters, BBC Urdu, AP, AFP Fact Check.

VERDICT CATEGORIES:
- "false": Claim directly contradicts verified sources
- "misleading": Claim is technically true but missing critical context that changes its meaning
- "unverified": No credible sources confirm or deny — not enough evidence either way
- "true": Confirmed by multiple independent credible sources
- "satire_misread": Content is satire or parody, being shared as genuine news
- "old_news_recycled": The event was real but happened in the past — being recirculated as current
- "out_of_context": Real image or event used to support a completely different, unrelated claim

FOR EACH CLAIM:
1. Write 1-2 targeted search queries
2. Execute web searches
3. Evaluate results against the claim
4. Assign truth_score 0-100 (0=definitely false, 50=unverifiable, 100=definitely true)
5. Cite the single most credible source found

RESPOND ONLY WITH VALID JSON. NO OTHER TEXT. NO MARKDOWN. EXACT STRUCTURE:
{
  "overall_verdict": "false",
  "overall_confidence": 88,
  "analysis_summary": "2-3 sentence plain English summary of what was found",
  "claims_analysis": [
    {
      "claim_id": "C1",
      "normalized_claim": "the claim that was checked",
      "truth_score": 8,
      "verdict": "false",
      "verdict_category": "false",
      "reasoning": "Specific explanation: what sources say vs. what the claim says",
      "sources_checked": ["Dawn.com", "Geo.tv"],
      "best_source": {
        "name": "Dawn",
        "url": "https://dawn.com/example",
        "headline": "relevant article headline"
      },
      "search_queries_used": ["PM Pakistan resigned 2024", "Pakistan PM resignation news"]
    }
  ],
  "spread_risk": "high",
  "spread_risk_reason": "Political claim with emotional trigger during election period — high viral potential"
}"""
        response, used_model = await generate_content_with_fallback(
            contents=json.dumps(reader_output),
            client=client,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[{"google_search": {}}],
            )
        )
        
        # Handle multiple content blocks (text + tool_use)
        text_blocks = []
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.text:
                    text_blocks.append(part.text)
        
        final_text = "".join(text_blocks).strip()
        if final_text.startswith("```json"):
            final_text = final_text[7:]
        if final_text.endswith("```"):
            final_text = final_text[:-3]
            
        if not final_text:
            raise ValueError("Empty response text from Analyst Agent")
            
        return json.loads(final_text)
    except Exception as e:
        print(f"Analyst Agent failed: {e}")
        # fallback
        return {
            "overall_verdict": "unverified",
            "overall_confidence": 0,
            "analysis_summary": "System currently experiencing high load. Please try again.",
            "claims_analysis": [
                {
                    "claim_id": "C1",
                    "normalized_claim": "Unknown (API Quota Exceeded)",
                    "truth_score": 0,
                    "verdict": "unverified",
                    "verdict_category": "unverified",
                    "reasoning": "We're sorry, but the AI verification system is currently over capacity. Please try again later.",
                    "sources_checked": [],
                    "best_source": {"name": "", "url": "", "headline": ""},
                    "search_queries_used": []
                }
            ],
            "spread_risk": "medium",
            "spread_risk_reason": "Fallback"
        }
