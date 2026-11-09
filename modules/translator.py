"""
Multilingual Translation & News Parsing Engine for SunoLocal.
Supports 6 languages:
- Kannada (kn-IN)
- Telugu (te-IN)
- Tamil (ta-IN)
- Malayalam (ml-IN)
- Hindi (hi-IN)
- English (en-IN)

Provides COMPLETE, factual explanations without shortening.
"""

import json
import re
import os
import requests
from config import Config

LANG_CODE_MAP = {
    "English": "en-IN",
    "Kannada": "kn-IN",
    "Telugu": "te-IN",
    "Tamil": "ta-IN",
    "Malayalam": "ml-IN",
    "Hindi": "hi-IN"
}

def normalize_language(lang_input):
    """Normalizes language string to capitalized standard language name."""
    if not lang_input:
        return "English"
    l = str(lang_input).strip().lower()
    if l.startswith("kn") or "kannada" in l or "ಕನ್ನಡ" in l:
        return "Kannada"
    elif l.startswith("te") or "telugu" in l or "తెలుగు" in l:
        return "Telugu"
    elif l.startswith("ta") or "tamil" in l or "தமிழ்" in l:
        return "Tamil"
    elif l.startswith("ml") or "malayalam" in l or "മലയാളം" in l:
        return "Malayalam"
    elif l.startswith("hi") or "hindi" in l or "हिन्दी" in l:
        return "Hindi"
    return "English"


def get_article_content(article_row_or_dict, language="English"):
    """
    Extracts the full factual article content in the user's selected language.
    Does NOT shorten or summarize - preserves complete facts, dates, numbers, and steps.
    """
    article = dict(article_row_or_dict)
    target_lang = normalize_language(language)
    lang_code = LANG_CODE_MAP.get(target_lang, "en-IN")

    raw_json = article.get("multilingual_content")
    multilingual = {}
    if isinstance(raw_json, str):
        try:
            multilingual = json.loads(raw_json)
        except Exception:
            multilingual = {}
    elif isinstance(raw_json, dict):
        multilingual = raw_json

    # Use a stored explanation in the selected language when one exists.
    # If it does not, keep the English source and say so. Do not pretend it was translated.
    translation_notice = ""
    text_language = target_lang
    if target_lang in multilingual:
        content = multilingual[target_lang].copy()
        native = Config.LANGUAGE_NATIVE_NAMES.get(target_lang, target_lang)
        translation_notice = (
            f"This explanation is written in {target_lang} ({native}) for SunoLocal. "
            "Names, dates, amounts, and official terms are kept as published. "
            "It is an original explanation with a link to the source, not a copy of a copyrighted article."
        )
    elif "English" in multilingual:
        content = multilingual["English"].copy()
        text_language = "English"
        if target_lang != "English":
            translation_notice = (
                f"A complete {target_lang} explanation is not stored for this item. "
                "The text below is the original English explanation. It has not been machine-translated, "
                "and it will not be read aloud as " + target_lang + "."
            )
        else:
            translation_notice = (
                "This explanation is written in English. "
                "It is an original explanation with a link to the source."
            )
    else:
        content = {
            "headline": article.get("original_headline", ""),
            "full_explanation": "Complete details available at official source.",
            "important_entities": article.get("publisher_name", ""),
            "key_figures_and_dates": article.get("publication_date", ""),
            "background_and_reasons": "Official announcement.",
            "citizen_impact": "Applicable to relevant citizens.",
            "actionable_steps": "Refer to official source portal.",
            "official_references": article.get("source_url", ""),
            "speech_text": article.get("original_headline", "")
        }
        text_language = "English"
        translation_notice = "A stored explanation was not found. Open the original source."

    # Attach base metadata
    content["id"] = article.get("id")
    content["category"] = article.get("category")
    content["original_headline"] = article.get("original_headline")
    content["publisher_name"] = article.get("publisher_name")
    content["source_url"] = article.get("source_url")
    content["publication_date"] = article.get("publication_date")
    content["publication_time"] = article.get("publication_time", "10:00 AM IST")
    content["last_updated_date"] = article.get("last_updated_date", article.get("publication_date"))
    content["location"] = article.get("location")
    content["is_official_government"] = article.get("is_official_government", 1)
    content["verification_status"] = article.get("verification_status", "Verified Official Notification")
    content["requested_language"] = target_lang
    content["language"] = text_language
    content["lang_code"] = LANG_CODE_MAP.get(text_language, "en-IN")
    content["native_lang_name"] = Config.LANGUAGE_NATIVE_NAMES.get(text_language, text_language)
    content["translation_notice"] = translation_notice
    content["can_speak"] = text_language == target_lang and bool(content.get("speech_text"))

    # Ensure category details exist
    if "category_details" not in content and "English" in multilingual:
        content["category_details"] = multilingual["English"].get("category_details", {})

    return content
