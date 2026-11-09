"""
Query Understanding & Intent Parser for SunoLocal.
Extracts user intent, category, location, and keywords from natural language questions
in both English and Kannada.
"""

import re
from config import Config

# Common stop-words and question filler patterns (English & Kannada)
QUESTION_FILLERS = [
    r"\bwhat\s+(is|are|were|was)\s+(the\s+)?(latest\s+|upcoming\s+|new\s+|available\s+)?",
    r"\btell\s+me\s+(about\s+)?(the\s+)?(latest\s+|upcoming\s+|any\s+)?",
    r"\bcan\s+you\s+(tell|show|give|find)\s+(me\s+)?(about\s+)?",
    r"\bwhere\s+can\s+i\s+(find|apply|get)\s+",
    r"\bhow\s+to\s+(apply\s+for|find|participate\s+in)\s+",
    r"\bshow\s+(me\s+)?(all\s+)?(the\s+)?(latest\s+|upcoming\s+)?",
    r"\bare\s+there\s+any\s+",
    r"\bwhich\s+(are|is)\s+(the\s+)?",
    r"\bplease\s+(find|show|give)\s+",
    r"\bdetails\s+(about|of|on)\s+",
    r"\binformation\s+(about|on|regarding)\s+",
    r"\bnews\s+(about|on)\s+",
    r"\blatest\b",
    r"\bupcoming\b",
    r"\bnew\b",
    r"\bavailable\b",
    r"\bcurrent\b",
    r"\bfor\b",
    r"\bin\b",
    r"\bat\b",
    r"\bof\b",
    r"\bthe\b",
    r"\ba\b",
    r"\ban\b",
    # Kannada question markers
    r"ಯಾವುವು\b",
    r"ಯಾವ\b",
    r"ಬಗ್ಗೆ\s+ತಿಳಿಸಿ\b",
    r"ಮಾಹಿತಿ\s+ನೀಡಿ\b",
    r"ಲಭ್ಯವಿರುವ\b",
    r"ಹೊಸ\b",
    r"ಇತ್ತೀಚಿನ\b",
    r"ಬಗ್ಗೆ\b",
    r"ತಿಳಿಸಿ\b"
]

# Location matching dictionary
LOCATION_SYNONYMS = {
    "mysuru": "Mysuru",
    "mysore": "Mysuru",
    "ಮೈಸೂರು": "Mysuru",
    "ಮೈಸೂರಿನಲ್ಲಿ": "Mysuru",
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "ಬೆಂಗಳೂರು": "Bengaluru",
    "mandya": "Mandya",
    "ಮಂಡ್ಯ": "Mandya",
    "karnataka": "Karnataka Statewide",
    "statewide": "Karnataka Statewide",
    "ಕರ್ನಾಟಕ": "Karnataka Statewide",
    "ಕರ್ನಾಟಕದ": "Karnataka Statewide",
    "all india": "All India",
    "india": "All India",
    "ಭಾರತ": "All India"
}

# Mapping keywords/regex to Core Categories
INTENT_CATEGORY_RULES = [
    # 1. Agriculture and farming
    (
        [
            r"\b(farmer|farmers|farming|agriculture|crop|crops|krishi|raitha|kisan|pm-kisan|raitha siri|krishi bhagya|fertilizer|seed|pesticide|soil|irrigation|tractor|horticulture|organic farming)\b",
            r"(ರೈತ|ರೈತರು|ರೈತರಿಗೆ|ಕೃಷಿ|ಬೆಳೆ|ಕಿಸಾನ್|ರೈತ ಸಿರಿ|ಕೃಷಿ ಭಾಗ್ಯ|ರಸಗೊಬ್ಬರ|ಬೀಜ|ತೋಟಗಾರಿಕೆ)"
        ],
        "Agriculture and farming"
    ),
    # 2. Sports and tournaments
    (
        [
            r"\b(cricket|football|sports|tournament|tournaments|ksca|badminton|athletics|hockey|kabaddi|championship|match|trophy|olympics|sports quota|coaching)\b",
            r"(ಕ್ರೀಡೆ|ಪಂದ್ಯಾವಳಿ|ಪಂದ್ಯಾವಳಿಗಳು|ಕ್ರಿಕೆಟ್|ಫುಟ್ಬಾಲ್|ಅಥ್ಲೆಟಿಕ್ಸ್|ಕಬಡ್ಡಿ|ಚಾಂಪಿಯನ್‌ಶಿಪ್)"
        ],
        "Sports and tournaments"
    ),
    # 3. Education and scholarships
    (
        [
            r"\b(scholarship|scholarships|ssp|nsp|vidyasiri|tuition fee|fee concession|merit scholarship|post matric|pre matric|fellowship|fellowships|engineering students? scholarship)\b",
            r"(ವಿದ್ಯಾರ್ಥಿವೇತನ|ವಿದ್ಯಾರ್ಥಿವೇತನಗಳು|ಎಸ್ಎಸ್ಪಿ|ಶುಲ್ಕ ವಿನಾಯಿತಿ|ಶಿಷ್ಯವೇತನ)"
        ],
        "Education and scholarships"
    ),
    # 4. Government schemes and announcements
    (
        [
            r"\b(government schemes?|govt schemes?|announcement|announcements|guarantee schemes?|seva sindhu|gruha lakshmi|yuva nidhi|shakti scheme|gruha jyothi|anna bhagya|subsid(y|ies)|gazette|circular)\b",
            r"(ಸರ್ಕಾರಿ ಯೋಜನೆ|ಸರ್ಕಾರದ ಯೋಜನೆಗಳು|ಯೋಜನೆಗಳು|ಸೇವಾ ಸಿಂಧು|ಗ್ಯಾರಂಟಿ|ಯುವನಿಧಿ|ಪ್ರಕಟಣೆ|ಸರ್ಕಾರ)"
        ],
        "Government schemes and announcements"
    ),
    # 5. Jobs and internships
    (
        [
            r"\b(jobs?|vacanc(y|ies)|recruitment|hiring|job opportunities|internships?|apprenticeships?|walk-in|career|placements?|kea recruitment|kpsc|beyond bengaluru job)\b",
            r"(ಉದ್ಯೋಗ|ಉದ್ಯೋಗಗಳು|ಕೆಲಸ|ನೇಮಕಾತಿ|ಇಂಟರ್ನ್‌ಶಿಪ್|ಖಾಲಿ ಹುದ್ದೆ)"
        ],
        "Jobs and internships"
    ),
    # 6. Technology and AI
    (
        [
            r"\b(ai\b|artificial intelligence|machine learning|deep tech|technology|software|coding|python|hackathon|kits|startup karnataka|it news|cybersecurity|iot)\b",
            r"(ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ|ತಂತ್ರಜ್ಞಾನ|ಎಐ|ಸಾಫ್ಟ್‌ವೇರ್|ಹ್ಯಾಕಥಾನ್|ತಾಂತ್ರಿಕ)"
        ],
        "Technology and AI"
    ),
    # 7. Business and startups
    (
        [
            r"\b(business|startups?|msme|entrepreneurs?|funding|seed fund|venture|incubation|knec|mudra loan|pmegp|commercial)\b",
            r"(ವ್ಯಾಪಾರ|ನವೋದ್ಯಮ|ಉದ್ಯಮ|ಸ್ಟಾರ್ಟಪ್|ಸಾಲ ಸೌಲಭ್ಯ|ವ್ಯವಹಾರ)"
        ],
        "Business and startups"
    ),
    # 8. Health and public awareness
    (
        [
            r"\b(health|hospital|medical|ayushman|arogya|tele-manas|mental health|vaccination|clinic|wellness|awareness|disease)\b",
            r"(ಆರೋಗ್ಯ|ಆಸ್ಪತ್ರೆ|ವೈದ್ಯಕೀಯ|ಆರೋಗ್ಯ ಕರ್ನಾಟಕ|ಲಸಿಕೆ|ಚಿಕಿತ್ಸೆ)"
        ],
        "Health and public awareness"
    ),
    # 9. Local news and politics
    (
        [
            r"\b(local news|politics|mcc|corporation|mysuru city corporation|election|civic|mla|mp|ward|panchayat|assembly)\b",
            r"(ಸ್ಥಳೀಯ ಸುದ್ದಿ|ರಾಜಕೀಯ|ಮೈಸೂರು ಮಹಾನಗರ ಪಾಲಿಕೆ|ಚುನಾವಣೆ|ಪಾಲಿಕೆ)"
        ],
        "Local news and politics"
    ),
    # 10. Weather and environment
    (
        [
            r"\b(weather|rain|monsoon|ksndmc|forecast|climate|temperature|chamundi hill|forest|pollution|flood|reservoir|lake)\b",
            r"(ಹವಾಮಾನ|ಮಳೆ|ಮಾನ್ಸೂನ್|ಪರಿಸರ|ತಾಪಮಾನ|ಕಾಡು|ಜಲಾಶಯ)"
        ],
        "Weather and environment"
    ),
    # 11. Events, festivals and competitions
    (
        [
            r"\b(competitions?|festivals?|events?|dasara|yuva dasara|yuva sambhrama|cultural|dance competition|quiz competition|exhibition)\b",
            r"(ಸ್ಪರ್ಧೆ|ಸ್ಪರ್ಧೆಗಳು|ಹಬ್ಬ|ದಸರಾ|ಯುವ ಸಂಭ್ರಮ|ಕಾರ್ಯಕ್ರಮ|ಮಹೋತ್ಸವ)"
        ],
        "Events, festivals and competitions"
    ),
    # 12. Women empowerment and welfare schemes
    (
        [
            r"\b(women|women empowerment|mahila|gruha lakshmi|udyogini|shg|self help group|stree shakti|girl child|bhagyalakshmi)\b",
            r"(ಮಹಿಳಾ|ಮಹಿಳೆಯರಿಗೆ|ಗೃಹಲಕ್ಷ್ಮಿ|ಉದ್ಯೋಗಿನಿ|ಸ್ತ್ರೀ ಶಕ್ತಿ|ಸ್ವಸಹಾಯ ಸಂಘ)"
        ],
        "Women empowerment and welfare schemes"
    ),
    # 13. Student opportunities
    (
        [
            r"\b(students?|student opportunities|college students?|engineering students?|pu college|university of mysore|vtu|degree students?)\b",
            r"(ವಿದ್ಯಾರ್ಥಿ|ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ|ಕಾಲೇಜು ವಿದ್ಯಾರ್ಥಿ|ವಿಶ್ವವಿದ್ಯಾಲಯ)"
        ],
        "Student opportunities"
    ),
    # 14. Skill development and training
    (
        [
            r"\b(skill development|training|bootcamp|gttc|ksdc|skill mission|drone training|technical training|vocational|upskilling)\b",
            r"(ಕೌಶಲ್ಯ|ತರಬೇತಿ|ಕೌಶಲ್ಯ ಅಭಿವೃದ್ಧಿ|ಬೂಟ್‌ಕ್ಯಾಂಪ್)"
        ],
        "Skill development and training"
    ),
    # 15. Entertainment and culture
    (
        [
            r"\b(entertainment|culture|theatre|drama|rangayana|heritage|music|sahitya|literature|cinema|kannada sahitya)\b",
            r"(ಮನರಂಜನೆ|ಸಂಸ್ಕೃತಿ|ರಂಗಾಯಣ|ನಾಟಕ|ಸಾಹಿತ್ಯ|ಸಂಗೀತ|ಪರಂಪರೆ)"
        ],
        "Entertainment and culture"
    )
]

def parse_user_query(query_text):
    """
    Analyzes natural language search text and extracts:
    - detected_category: One of the 15 categories, or None if broad/unknown
    - detected_location: e.g. 'Mysuru', 'Karnataka Statewide', or None
    - clean_keywords: List of meaningful content tokens
    - is_kannada: Boolean flag
    - interpreted_summary: Human-readable interpretation explanation
    - confidence: float score (0.0 to 1.0)
    """
    raw = (query_text or "").strip()
    if not raw:
        return {
            "raw_query": "",
            "detected_category": None,
            "detected_location": None,
            "clean_keywords": [],
            "is_kannada": False,
            "interpreted_summary": "",
            "confidence": 0.0
        }

    # Detect if query has Kannada script (Unicode range \u0C80-\u0CFF)
    is_kannada = bool(re.search(r"[\u0C80-\u0CFF]", raw))

    lower_query = raw.lower()

    # 1. Location Detection
    detected_location = None
    for loc_key, loc_canonical in LOCATION_SYNONYMS.items():
        if loc_key in lower_query:
            detected_location = loc_canonical
            break

    # 2. Category Detection via Intent Rules
    detected_category = None
    matched_rule_score = 0

    for patterns, category_name in INTENT_CATEGORY_RULES:
        for pat in patterns:
            if re.search(pat, lower_query, re.IGNORECASE):
                detected_category = category_name
                matched_rule_score = 1.0
                break
        if detected_category:
            break

    # If direct rule didn't hit, check Config.CATEGORY_CANONICAL_MAP
    if not detected_category:
        for alias, canon in Config.CATEGORY_CANONICAL_MAP.items():
            if alias in lower_query:
                detected_category = canon
                matched_rule_score = 0.8
                break

    # 3. Clean keywords (strip question fillers and punctuation)
    cleaned = lower_query
    for filler in QUESTION_FILLERS:
        cleaned = re.sub(filler, " ", cleaned, flags=re.IGNORECASE)

    # Remove location name from keywords to avoid duplicate constraints
    if detected_location:
        for loc_key in LOCATION_SYNONYMS.keys():
            cleaned = re.sub(r"\b" + re.escape(loc_key) + r"\b", " ", cleaned)

    # Clean non-alphanumeric (keep Kannada characters and spaces)
    cleaned = re.sub(r"[^\w\s\u0C80-\u0CFF]", " ", cleaned)
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]

    # Filter out residual tiny words
    common_short = {"to", "in", "of", "on", "at", "by", "is", "it", "or", "and", "the", "for"}
    clean_keywords = [t for t in tokens if t not in common_short]

    # Human-readable interpretation explanation
    summary_parts = []
    if detected_category:
        cat_meta = Config.CATEGORY_METADATA.get(detected_category, {})
        cat_display = f"{detected_category} ({cat_meta.get('kannada', '')})" if is_kannada and cat_meta else detected_category
        summary_parts.append(f"Category: {cat_display}")
    if detected_location:
        summary_parts.append(f"Location: {detected_location}")
    if clean_keywords:
        summary_parts.append(f"Keywords: {', '.join(clean_keywords[:4])}")

    interpreted_summary = " • ".join(summary_parts) if summary_parts else "Broad search across all categories"

    return {
        "raw_query": raw,
        "detected_category": detected_category,
        "detected_location": detected_location,
        "clean_keywords": clean_keywords,
        "is_kannada": is_kannada,
        "interpreted_summary": interpreted_summary,
        "confidence": matched_rule_score if detected_category else (0.5 if clean_keywords else 0.1)
    }
