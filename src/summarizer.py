"""
Summariser — sends fetched items to an LLM and gets back a structured digest.
Primary: Gemini 2.0 Flash (free tier, generous daily limit).
Fallback: Groq Llama 3.3 70B (also free — uses the openai SDK pointed at Groq's URL).
Direct API calls only — no LangChain, no abstractions, as per project rules.
"""
import json
import os

import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Gemini 2.0 Flash (not 2.5) — 2.5 Flash defaults to "extended thinking", which
# can silently take minutes per call on the google-generativeai 0.8.x SDK
# (no thinking_budget knob available). 2.0 Flash answers directly and is just
# as capable for this structured-extraction task.
GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
# Groq exposes an OpenAI-compatible endpoint, so we reuse the openai SDK
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# 40 items keeps the prompt under ~6K tokens — fast and well within free-tier limits
MAX_ITEMS_FOR_PROMPT = 40


def _build_prompt(items: list[dict], digest_time: str) -> str:
    """
    Construct the LLM prompt with all fetched items embedded.
    digest_time controls which framing the LLM should use (morning vs evening).
    We explicitly ask for JSON-only output to avoid markdown wrapping the response.
    """
    items_text = "\n".join(
        f"{i+1}. [{item['source']}] {item['title']}\n"
        f"   URL: {item['url']}\n"
        f"   {item.get('summary','')[:200]}"
        for i, item in enumerate(items[:MAX_ITEMS_FOR_PROMPT])
    )

    evening_instruction = (
        "This is the EVENING digest. Frame top_stories as 'what happened since morning'. "
        "Keep community_discussions updated with the latest sentiment."
        if digest_time == "evening"
        else ""
    )

    return f"""You are an AI/ML news curator building a daily digest for a backend engineer.
{evening_instruction}

Here are today's fetched items ({min(len(items), MAX_ITEMS_FOR_PROMPT)} items):

{items_text}

Return ONLY a valid JSON object — no markdown fences, no explanation, just JSON.
Use this exact schema:

{{
  "top_stories": [
    {{"title": "...", "what_it_is": "...", "why_it_matters": "...", "what_changed": "...", "url": "...", "source": "..."}}
  ],
  "new_models": [
    {{"name": "...", "type": "...", "what_it_is": "...", "improvement_over_previous": "...", "url": "..."}}
  ],
  "new_tools_frameworks": [
    {{"name": "...", "category": "...", "what_it_does": "...", "why_better_than_alternatives": "...", "url": "..."}}
  ],
  "community_discussions": [
    {{"topic": "...", "sentiment": "excited|concerned|skeptical|mixed", "key_points": "...", "source": "...", "url": "..."}}
  ],
  "research_papers": [
    {{"title": "...", "plain_english": "...", "key_contribution": "...", "url": "..."}}
  ],
  "techniques_approaches": [
    {{"name": "...", "what_it_does": "...", "improvement_over_before": "...", "url": "..."}}
  ],
  "trending_topics": ["topic1", "topic2"],
  "digest_summary": "2-3 sentence overview of today in AI/ML"
}}

Rules:
- top_stories: 3-5 items, most impactful first
- new_models: only actual model releases; empty array [] if none today
- sentiment MUST be exactly one of: excited, concerned, skeptical, mixed
- trending_topics: 5-8 short tag strings
- For EVERY item, explain HOW it improves over the previous approach
- Plain English — explain jargon when you use it
- Return ONLY the JSON object, nothing else"""


def _strip_fences(raw: str) -> str:
    """
    Strip markdown code fences if the model wraps its output in ```json ... ```.
    Some models add these despite being told not to.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        # Remove opening fence line (e.g. ```json or ```)
        lines = raw.split("\n")
        lines = lines[1:]  # drop first line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # drop closing fence
        raw = "\n".join(lines)
    return raw.strip()


def _call_gemini(prompt: str) -> dict:
    """
    Call Gemini 2.0 Flash. Raises on failure so the caller can fall back to Groq.
    response_mime_type="application/json" nudges the model to return raw JSON
    (still passed through _strip_fences as a safety net for any stray fences).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        ),
    )

    return json.loads(_strip_fences(response.text))


def _call_groq(prompt: str) -> dict:
    """
    Call Groq Llama 3.3 70B via the OpenAI-compatible endpoint.
    lower temperature (0.3) produces more consistent JSON structure.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4096,
    )

    return json.loads(_strip_fences(response.choices[0].message.content))


def _empty_digest() -> dict:
    """Minimal valid digest returned when both LLM calls fail."""
    return {
        "top_stories": [],
        "new_models": [],
        "new_tools_frameworks": [],
        "community_discussions": [],
        "research_papers": [],
        "techniques_approaches": [],
        "trending_topics": [],
        "digest_summary": "Digest generation failed — check GEMINI_API_KEY / GROQ_API_KEY and logs.",
    }


def summarize(items: list[dict], digest_time: str = "morning") -> dict:
    """
    Run the summarisation pipeline: build prompt → try Gemini → fall back to Groq.
    Returns the structured digest dict, or a minimal fallback dict if both fail.
    digest_time should be 'morning' or 'evening'.
    """
    if not items:
        print("[Summarizer] No items to summarize — returning empty digest")
        return _empty_digest()

    prompt = _build_prompt(items, digest_time)

    try:
        print(f"[Summarizer] Calling Gemini ({GEMINI_MODEL})...")
        result = _call_gemini(prompt)
        print("[Summarizer] Gemini succeeded")
        return result
    except Exception as e:
        print(f"[Summarizer] Gemini failed ({e}) — falling back to Groq")

    try:
        print(f"[Summarizer] Calling Groq ({GROQ_MODEL})...")
        result = _call_groq(prompt)
        print("[Summarizer] Groq succeeded")
        return result
    except Exception as e:
        print(f"[Summarizer] Groq also failed ({e}) — returning empty digest")

    return _empty_digest()
