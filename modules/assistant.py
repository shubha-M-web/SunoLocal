"""
Answers questions about one stored article.

Uses Gemini only when GEMINI_API_KEY is set. Otherwise a labelled fallback
reads fields already stored for that article. It does not invent eligibility,
amounts, or deadlines.
"""

import os
import json
import requests

from config import Config
from modules.translator import get_article_content, normalize_language

DISCLAIMER = (
    "This is general guidance from the information stored in SunoLocal. "
    "It is not an official government decision and it does not decide whether you are legally eligible. "
    "Confirm details on the official source before you apply or pay any fee."
)


def answer_question(article_row, question, language="English"):
    question = (question or "").strip()
    if not question:
        return _result(
            "Please type a question about this item.",
            [],
            "fallback",
            language,
        )

    content = get_article_content(article_row, language)
    text_language = content.get("language", "English")
    sources = _sources(article_row, content)

    gemini_key = Config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            live = _call_gemini(content, question, text_language, gemini_key)
            if live:
                live["sources"] = sources
                live["disclaimer"] = DISCLAIMER
                return live
        except Exception as exc:
            print(f"[Assistant] Gemini skipped ({exc}). Using stored-content fallback.")

    answer = _fallback_answer(content, question)
    return _result(answer, sources, "fallback", text_language, content.get("translation_notice"))


def _result(answer, sources, mode, language, notice=None):
    prefix = ""
    if mode == "fallback":
        prefix = (
            "Fallback explanation (no AI API key is configured). "
            "The answer uses only the text stored for this item. "
        )
    if notice:
        prefix += notice + " "
    return {
        "answer": prefix + answer,
        "sources": sources,
        "mode": mode,
        "language": language,
        "disclaimer": DISCLAIMER,
    }


def _sources(article_row, content):
    article = dict(article_row)
    refs = []
    if article.get("publisher_name"):
        refs.append({
            "label": article.get("publisher_name"),
            "url": article.get("source_url") or "",
        })
    official = content.get("official_references")
    if official and official != "Not available in the source":
        refs.append({"label": official, "url": ""})
    return refs


def _field(content, key):
    value = (content.get(key) or "").strip()
    if not value:
        return "Not available in the source."
    return value


def _details_text(content):
    details = content.get("category_details") or {}
    if not isinstance(details, dict) or not details:
        return ""
    lines = []
    for key, value in details.items():
        label = key.replace("_", " ")
        lines.append(f"{label}: {value if value else 'Not available in the source'}")
    return " ".join(lines)


def _fallback_answer(content, question):
    q = question.lower()
    details = _details_text(content)
    parts = []

    if any(word in q for word in ("eligib", "who can", "ಅರ್ಹ", "योग्य", "apply for")):
        parts.append("Eligibility from the stored record: " + _field(content, "citizen_impact"))
        if details:
            parts.append(details)
    elif any(word in q for word in ("document", "paper", "ದಾಖಲೆ", "दस्तावेज", "prepare")):
        parts.append("What the record says to prepare: " + _field(content, "actionable_steps"))
    elif any(word in q for word in ("deadline", "last date", "ಗಡುವು", "अंतिम", "when")):
        parts.append("Dates and figures in the record: " + _field(content, "key_figures_and_dates"))
        if details:
            parts.append(details)
    elif any(word in q for word in ("impact", "farmer", "affect", "benefit", "consequence")):
        parts.append("Who is affected, as stated in the record: " + _field(content, "citizen_impact"))
    elif any(word in q for word in ("next", "what should", "how to", "procedure", "apply")):
        parts.append("Steps recorded for this item: " + _field(content, "actionable_steps"))
    elif any(word in q for word in ("source", "official", "link")):
        parts.append("Publisher: " + _field(content, "publisher_name"))
        parts.append("Reference: " + _field(content, "official_references"))
        parts.append("Link: " + _field(content, "source_url"))
    else:
        parts.append(_field(content, "headline"))
        parts.append(_field(content, "full_explanation"))
        parts.append("Important dates and figures: " + _field(content, "key_figures_and_dates"))
        parts.append("What to do next: " + _field(content, "actionable_steps"))

    parts.append("If a detail is not written above, it is not available in the source stored by SunoLocal.")
    return " ".join(parts)


def _call_gemini(content, question, language, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "headline": content.get("headline"),
        "explanation": content.get("full_explanation"),
        "entities": content.get("important_entities"),
        "figures": content.get("key_figures_and_dates"),
        "background": content.get("background_and_reasons"),
        "impact": content.get("citizen_impact"),
        "steps": content.get("actionable_steps"),
        "references": content.get("official_references"),
        "details": content.get("category_details"),
        "source_url": content.get("source_url"),
        "publisher": content.get("publisher_name"),
    }
    prompt = f"""
You answer questions about one SunoLocal information item.
Use ONLY the JSON record below. If a fact is missing, say "Not available in the source".
Do not invent eligibility, money amounts, or deadlines.
Do not say the user is officially eligible.
Do not present your answer as a government announcement.
Answer in {language}.

Record:
{json.dumps(payload, ensure_ascii=False)}

Question: {question}
"""
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        },
        timeout=12,
    )
    if response.status_code != 200:
        return None
    body = response.json()
    text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
    return {
        "answer": "AI answer based on the stored record (Google Gemini). " + text,
        "mode": "gemini",
        "language": language,
    }
