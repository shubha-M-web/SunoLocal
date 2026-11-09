"""Interface labels for the six SunoLocal languages. Article text is stored separately."""

from config import Config

UI = {
    "English": {
        "home": "Home", "discover": "Discover", "news": "News & Updates",
        "sports": "Sports", "farming": "Farming", "government": "Government Rules",
        "politics": "Politics", "education": "Education", "saved": "Saved",
        "hub": "My Hub", "settings": "Settings", "technology": "Technology",
        "local": "Local", "business": "Business", "listen": "Listen",
        "save": "Save", "saved_state": "Saved", "search": "Search",
        "notifications": "Alerts", "assistant": "Ask about this",
        "demo_note": "Demonstration record", "live_note": "Live feed item",
        "original": "Original source", "not_available": "Not available in the source",
    },
    "Kannada": {
        "home": "ಮುಖಪುಟ", "discover": "ಹುಡುಕಿ", "news": "ಸುದ್ದಿ ಮತ್ತು ಅಪ್‌ಡೇಟ್",
        "sports": "ಕ್ರೀಡೆ", "farming": "ಕೃಷಿ", "government": "ಸರ್ಕಾರಿ ನಿಯಮಗಳು",
        "politics": "ರಾಜಕೀಯ", "education": "ಶಿಕ್ಷಣ", "saved": "ಉಳಿಸಿದವು",
        "hub": "ನನ್ನ ಕೇಂದ್ರ", "settings": "ಸೆಟ್ಟಿಂಗ್", "technology": "ತಂತ್ರಜ್ಞಾನ",
        "local": "ಸ್ಥಳೀಯ", "business": "ವ್ಯಾಪಾರ", "listen": "ಕೇಳಿ",
        "save": "ಉಳಿಸಿ", "saved_state": "ಉಳಿಸಲಾಗಿದೆ", "search": "ಹುಡುಕಿ",
        "notifications": "ಎಚ್ಚರಿಕೆಗಳು", "assistant": "ಇದರ ಬಗ್ಗೆ ಕೇಳಿ",
        "demo_note": "ಪ್ರದರ್ಶನ ದಾಖಲೆ", "live_note": "ನೇರ ಫೀಡ್",
        "original": "ಮೂಲ ಮೂಲ", "not_available": "ಮೂಲದಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ",
    },
    "Telugu": {
        "home": "హోమ్", "discover": "కనుగొనండి", "news": "వార్తలు",
        "sports": "క్రీడలు", "farming": "వ్యవసాయం", "government": "ప్రభుత్వ నియమాలు",
        "politics": "రాజకీయాలు", "education": "విద్య", "saved": "సేవ్ చేసినవి",
        "hub": "నా హబ్", "settings": "సెట్టింగ్‌లు", "technology": "సాంకేతికం",
        "local": "స్థానికం", "business": "వ్యాపారం", "listen": "వినండి",
        "save": "సేవ్", "saved_state": "సేవ్ అయింది", "search": "శోధన",
        "notifications": "హెచ్చరికలు", "assistant": "దీని గురించి అడగండి",
        "demo_note": "ప్రదర్శన రికార్డు", "live_note": "లైవ్ ఫీడ్",
        "original": "అసలు మూలం", "not_available": "మూలంలో లభ్యం కాదు",
    },
    "Tamil": {
        "home": "முகப்பு", "discover": "கண்டறி", "news": "செய்திகள்",
        "sports": "விளையாட்டு", "farming": "விவசாயம்", "government": "அரசு விதிகள்",
        "politics": "அரசியல்", "education": "கல்வி", "saved": "சேமித்தவை",
        "hub": "என் மையம்", "settings": "அமைப்புகள்", "technology": "தொழில்நுட்பம்",
        "local": "உள்ளூர்", "business": "வணிகம்", "listen": "கேளுங்கள்",
        "save": "சேமி", "saved_state": "சேமிக்கப்பட்டது", "search": "தேடு",
        "notifications": "எச்சரிக்கைகள்", "assistant": "இதைப் பற்றி கேளுங்கள்",
        "demo_note": "செயல்விளக்க பதிவு", "live_note": "நேரடி ஊட்டம்",
        "original": "மூல ஆதாரம்", "not_available": "மூலத்தில் இல்லை",
    },
    "Malayalam": {
        "home": "ഹോം", "discover": "കണ്ടെത്തുക", "news": "വാർത്തകൾ",
        "sports": "കായികം", "farming": "കൃഷി", "government": "സർക്കാർ നിയമങ്ങൾ",
        "politics": "രാഷ്ട്രീയം", "education": "വിദ്യാഭ്യാസം", "saved": "സേവ് ചെയ്തവ",
        "hub": "എന്റെ ഹബ്", "settings": "ക്രമീകരണം", "technology": "സാങ്കേതികം",
        "local": "പ്രാദേശികം", "business": "ബിസിനസ്", "listen": "കേൾക്കുക",
        "save": "സേവ്", "saved_state": "സേവ് ചെയ്തു", "search": "തിരയുക",
        "notifications": "മുന്നറിയിപ്പുകൾ", "assistant": "ഇതിനെക്കുറിച്ച് ചോദിക്കുക",
        "demo_note": "പ്രദർശന രേഖ", "live_note": "തത്സമയ ഫീഡ്",
        "original": "യഥാർത്ഥ സ്രോതസ്", "not_available": "സ്രോതസിൽ ലഭ്യമല്ല",
    },
    "Hindi": {
        "home": "होम", "discover": "खोजें", "news": "समाचार और अपडेट",
        "sports": "खेल", "farming": "कृषि", "government": "सरकारी नियम",
        "politics": "राजनीति", "education": "शिक्षा", "saved": "सहेजे गए",
        "hub": "मेरा हब", "settings": "सेटिंग्स", "technology": "तकनीक",
        "local": "स्थानीय", "business": "व्यापार", "listen": "सुनें",
        "save": "सहेजें", "saved_state": "सहेजा गया", "search": "खोज",
        "notifications": "सूचनाएँ", "assistant": "इसके बारे में पूछें",
        "demo_note": "प्रदर्शन रिकॉर्ड", "live_note": "लाइव फ़ीड",
        "original": "मूल स्रोत", "not_available": "स्रोत में उपलब्ध नहीं",
    },
}


def ui_for(language):
    return UI.get(language, UI["English"])


def html_lang(language):
    code = Config.LANGUAGE_CODES.get(language, "en-IN")
    return code.split("-")[0]
