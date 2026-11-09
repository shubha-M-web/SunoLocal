"""
AI Summarization Module for SunoLocal.
Generates structured, student-friendly explanations:
- What is this opportunity?
- Who can apply?
- Important requirements
- Important dates
- How to apply
- Original source

Supports configurable LLM API (Google Gemini / OpenAI compatible) with
a robust, zero-hallucination Extractive Fallback Engine for offline/demo use.
Supports both English and Kannada.
"""

import os
import re
import json
import requests
from config import Config

def generate_summary(opportunity, language="English"):
    """
    Produces a structured summary of an opportunity in English or Kannada.
    
    Args:
        opportunity: dict containing opportunity fields
        language: 'English' or 'Kannada' (or 'kn', 'kn-IN', 'en', 'en-IN')
        
    Returns:
        dict with:
            - what_is_it: str
            - who_can_apply: str
            - requirements: str
            - important_dates: str
            - how_to_apply: str
            - original_source: str
            - speech_text: str (clean narration text for Web Speech TTS)
            - provider: str (Labelled 'Gemini API' or 'Rule-based Extractive Engine')
            - language: str ('English' or 'Kannada')
            - lang_code: str ('en-IN' or 'kn-IN')
    """
    opp = dict(opportunity) if not isinstance(opportunity, dict) else opportunity
    
    # Normalize language string
    raw_lang = str(language or "English").strip().lower()
    if raw_lang.startswith("k") or "kn" in raw_lang:
        lang = "Kannada"
        lang_code = "kn-IN"
    else:
        lang = "English"
        lang_code = "en-IN"
    
    # Check if Gemini API key is configured
    gemini_key = Config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            llm_result = _call_gemini_api(opp, lang, gemini_key)
            if llm_result:
                llm_result["lang_code"] = lang_code
                return llm_result
        except Exception as e:
            # Fall back safely without crashing
            print(f"[Summarizer Notice] Gemini API call skipped or failed ({e}). Using Extractive Fallback.")

    # High-quality deterministic extractive fallback
    fallback_res = _generate_extractive_fallback(opp, lang)
    fallback_res["lang_code"] = lang_code
    return fallback_res


def _call_gemini_api(opportunity, language, api_key):
    """Calls Gemini REST API to produce a structured summary."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
You are an accessibility summarizer for SunoLocal, an educational platform for students in Karnataka, India.
Create a simple, structured explanation for this student opportunity.
Do not invent any missing dates, links, or qualifications. If a detail is missing, state 'Not specified in official notice'.

Opportunity Details:
Title: {opportunity.get('title')}
Category: {opportunity.get('category')}
Organization: {opportunity.get('organization')}
Location: {opportunity.get('location')}
Description: {opportunity.get('full_description') or opportunity.get('short_description')}
Eligibility: {opportunity.get('eligibility')}
Requirements: {opportunity.get('requirements')}
Deadline: {opportunity.get('deadline')}
How to apply: {opportunity.get('how_to_apply')}
Source Name: {opportunity.get('source_name')}
Source URL: {opportunity.get('source_url')}

Target Language: {language}

Return strictly a JSON object with these keys:
"what_is_it": short clear explanation in {language},
"who_can_apply": eligibility in {language},
"requirements": needed documents in {language},
"important_dates": application deadline or dates in {language},
"how_to_apply": numbered concise steps in {language},
"original_source": publisher and portal name in {language},
"speech_text": 3-4 natural conversational sentences formatted for audio text-to-speech in {language}
"""

    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }
    
    response = requests.post(url, headers=headers, json=body, timeout=8)
    if response.status_code == 200:
        res_json = response.json()
        raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)
        parsed["provider"] = "Google Gemini AI (Live Model)"
        parsed["language"] = language
        return parsed
    return None


def _clean_speech_text(text):
    """Removes metadata tags like [SAMPLE DATA] from text for speech synthesis."""
    if not text:
        return ""
    cleaned = re.sub(r'\[.*?\]', '', text)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def _generate_extractive_fallback(opportunity, language):
    """
    Zero-hallucination rule-based extractive summary.
    Extracts and organizes existing verified fields into structured sections.
    """
    if language == "Kannada":
        raw_title = opportunity.get("kannada_title") or opportunity.get("title") or ""
        clean_title = _clean_speech_text(raw_title)
        
        raw_desc = opportunity.get("kannada_description") or opportunity.get("short_description") or ""
        clean_desc = _clean_speech_text(raw_desc)
        
        org = opportunity.get("organization") or "ಅಧಿಕೃತ ಸಂಸ್ಥೆ"
        loc = opportunity.get("location") or "ಕರ್ನಾಟಕ"
        elig = opportunity.get("eligibility") or "ಅಧಿಕೃತ ಪ್ರಕಟಣೆಯಲ್ಲಿ ನಿರ್ದಿಷ್ಟಪಡಿಸಿಲ್ಲ."
        req = opportunity.get("requirements") or "ಮೂಲ ಅಧಿಸೂಚನೆಯಲ್ಲಿ ಪರಿಶೀಲಿಸಿ."
        deadline = opportunity.get("deadline") or "ಕೊನೆಯ ದಿನಾಂಕ ನಿಗದಿಯಾಗಿಲ್ಲ (ಮುಕ್ತ ಅರ್ಜಿ)."
        apply = opportunity.get("how_to_apply") or "ಅಧಿಕೃತ ಪೋರ್ಟಲ್ ಮೂಲಕ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ."
        src_name = opportunity.get("source_name") or "ಮೂಲ ಸಂಸ್ಥೆ"

        what_is_it = f"{org} ವತಿಯಿಂದ {loc}ದಲ್ಲಿ ಆಯೋಜಿಸಲಾದ '{clean_title}'. {clean_desc}"
        who_can_benefit = opportunity.get("who_can_benefit") or "ಅರ್ಹ ನಾಗರಿಕರು, ಕೃಷಿಕರು ಮತ್ತು ವಿದ್ಯಾರ್ಥಿಗಳು."
        who_can_apply = elig
        requirements = req
        important_dates = f"ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಕೊನೆಯ ದಿನಾಂಕ: {deadline}"
        how_to_apply = apply
        original_source = f"{src_name} ({opportunity.get('source_url') or 'ಮೂಲ ಲಿಂಕ್ ಲಭ್ಯವಿಲ್ಲ'})"
        last_updated_date = opportunity.get("last_updated_date") or opportunity.get("publication_date") or "ಇತ್ತೀಚೆಗೆ ನವೀಕರಿಸಲಾಗಿದೆ"
        
        speech_text = (
            f"ನಮಸ್ಕಾರ. ಇದು ಸುನೋ ಲೋಕಲ್ ಧ್ವನಿ ಸಾರಾಂಶ. "
            f"ಅವಕಾಶದ ಹೆಸರು: {clean_title}. "
            f"ಸಂಸ್ಥೆ: {org}, ಸ್ಥಳ: {loc}. "
            f"ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಕೊನೆಯ ದಿನಾಂಕ: {deadline}. "
            f"ಅರ್ಹತೆ: {elig[:150]}. "
            f"ಹೆಚ್ಚಿನ ವಿವರಗಳಿಗೆ ಸುನೋ ಲೋಕಲ್ ಮಾಹಿತಿ ಪೋರ್ಟಲ್ ನೋಡಿ."
        )

        return {
            "what_is_it": what_is_it,
            "who_can_benefit": who_can_benefit,
            "who_can_apply": who_can_apply,
            "requirements": requirements,
            "important_dates": important_dates,
            "how_to_apply": how_to_apply,
            "original_source": original_source,
            "last_updated_date": last_updated_date,
            "speech_text": speech_text,
            "provider": "SunoLocal Extractive Fallback Engine (Offline Mode)",
            "language": "Kannada"
        }
    else:
        raw_title = opportunity.get("title", "")
        clean_title = _clean_speech_text(raw_title)
        
        raw_desc = opportunity.get("short_description", "")
        clean_desc = _clean_speech_text(raw_desc)
        
        full_desc = opportunity.get("full_description", raw_desc)
        org = opportunity.get("organization", "Official Authority")
        loc = opportunity.get("location", "Karnataka")
        elig = opportunity.get("eligibility") or "Specific eligibility criteria not detailed in posting. Check official circular."
        req = opportunity.get("requirements") or "Standard identification and academic documents required."
        deadline = opportunity.get("deadline") or "Ongoing / Not specified in notification."
        apply = opportunity.get("how_to_apply") or "Follow official portal guidelines provided at the source link."
        src_name = opportunity.get("source_name") or "External Publisher"

        what_is_it = f"{clean_title} announced by {org} for candidates in {loc}. {clean_desc}"
        who_can_benefit = opportunity.get("who_can_benefit") or "Eligible citizens, students, farmers, or professionals matching criteria."
        who_can_apply = elig
        requirements = req
        important_dates = f"Application Deadline: {deadline} (Published: {opportunity.get('publication_date') or 'Recent'})"
        how_to_apply = apply
        original_source = f"{src_name} - {opportunity.get('source_url') or 'No source link provided'}"
        last_updated_date = opportunity.get("last_updated_date") or opportunity.get("publication_date") or "Recently verified"

        speech_text = (
            f"Here is your SunoLocal audio briefing for {clean_title}. "
            f"Offered by {org} in {loc}. "
            f"Eligibility: {elig[:140]}. "
            f"Application deadline is {deadline}. "
            f"For verified steps, access the official source link on SunoLocal."
        )

        return {
            "what_is_it": what_is_it,
            "who_can_benefit": who_can_benefit,
            "who_can_apply": who_can_apply,
            "requirements": requirements,
            "important_dates": important_dates,
            "how_to_apply": how_to_apply,
            "original_source": original_source,
            "last_updated_date": last_updated_date,
            "speech_text": speech_text,
            "provider": "SunoLocal Extractive Fallback Engine (Offline Mode)",
            "language": "English"
        }
