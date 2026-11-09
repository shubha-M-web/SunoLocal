import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables if .env file exists
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sunolocal-innovate-hackathon-key-2026")
    DATABASE_PATH = str(INSTANCE_DIR / "sunolocal.db")
    
    # Optional LLM API keys for AI Summarization and Live Translation
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    
    # Defaults for Karnataka / Mysuru focus
    DEFAULT_LOCATION = "Mysuru"
    DEFAULT_LANGUAGE = "English"
    
    AVAILABLE_LOCATIONS = [
        "Mysuru",
        "Bengaluru",
        "Mandya",
        "Other Karnataka",
        "Karnataka Statewide",
        "All India"
    ]

    AVAILABLE_STATES = [
        "Karnataka",
        "Tamil Nadu",
        "Kerala",
        "Andhra Pradesh",
        "Telangana",
        "Maharashtra",
        "Delhi",
        "Other"
    ]

    # A suggestion only. The user always chooses the language.
    STATE_LANGUAGE_SUGGESTION = {
        "Karnataka": "Kannada",
        "Tamil Nadu": "Tamil",
        "Kerala": "Malayalam",
        "Andhra Pradesh": "Telugu",
        "Telangana": "Telugu",
        "Maharashtra": "Hindi",
        "Delhi": "Hindi",
        "Other": "English"
    }

    USER_TYPES = [
        ("student", "Student"),
        ("farmer", "Farmer"),
        ("job_seeker", "Job seeker"),
        ("professional", "Working professional"),
        ("citizen", "General citizen")
    ]

    USER_TYPE_NEWS = {
        "student": ["Education", "Sports", "Government Rules"],
        "farmer": ["Agriculture", "Government Rules", "Local and Community"],
        "job_seeker": ["Education", "Business and Economy", "Government Rules"],
        "professional": ["Technology and Science", "Business and Economy", "Government Rules"],
        "citizen": ["Local and Community", "Government Rules", "Politics", "Sports"]
    }
    
    # Core 15 Comprehensive Categories (with extensible support for ANY category)
    CORE_CATEGORIES = [
        "Agriculture and farming",
        "Sports and tournaments",
        "Education and scholarships",
        "Government schemes and announcements",
        "Jobs and internships",
        "Technology and AI",
        "Business and startups",
        "Health and public awareness",
        "Local news and politics",
        "Weather and environment",
        "Events, festivals and competitions",
        "Women empowerment and welfare schemes",
        "Student opportunities",
        "Skill development and training",
        "Entertainment and culture"
    ]

    CATEGORY_METADATA = {
        "Agriculture and farming": {
            "slug": "agriculture",
            "kannada": "ಕೃಷಿ ಮತ್ತು ರೈತ ಕಲ್ಯಾಣ",
            "icon": "bi-flower1",
            "color": "#2e7d32",
            "description": "Farming schemes, subsidies, crop insurance, organic farming, and agricultural advisories.",
            "synonyms": ["farming", "farmer", "agriculture", "krishi", "crops", "raitha", "pm-kisan", "seeds", "fertilizer", "ಕೃಷಿ", "ರೈತ"]
        },
        "Sports and tournaments": {
            "slug": "sports",
            "kannada": "ಕ್ರೀಡೆ ಮತ್ತು ಪಂದ್ಯಾವಳಿಗಳು",
            "icon": "bi-trophy",
            "color": "#e65100",
            "description": "Cricket, football, athletics, university games, state tournaments, and coaching trials.",
            "synonyms": ["sports", "cricket", "tournament", "athletics", "football", "badminton", "ksca", "olympic", "ಪಂದ್ಯಾವಳಿ", "ಕ್ರೀಡೆ", "ಕ್ರಿಕೆಟ್"]
        },
        "Education and scholarships": {
            "slug": "education",
            "kannada": "ಶಿಕ್ಷಣ ಮತ್ತು ವಿದ್ಯಾರ್ಥಿವೇತನ",
            "icon": "bi-mortarboard",
            "color": "#1565c0",
            "description": "Post-matric scholarships, fee concessions, engineering grants, and admission notices.",
            "synonyms": ["scholarship", "education", "ssp", "nsp", "engineering", "tuition", "fellowship", "ವಿದ್ಯಾರ್ಥಿವೇತನ", "ಶಿಕ್ಷಣ"]
        },
        "Government schemes and announcements": {
            "slug": "government",
            "kannada": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಮತ್ತು ಪ್ರಕಟಣೆಗಳು",
            "icon": "bi-bank",
            "color": "#00695c",
            "description": "Karnataka guarantee schemes, Seva Sindhu services, citizen welfare notices, and state policies.",
            "synonyms": ["government", "scheme", "seva sindhu", "guarantee", "announcement", "sarkari", "yuva nidhi", "ಸರ್ಕಾರ", "ಯೋಜನೆ"]
        },
        "Jobs and internships": {
            "slug": "jobs",
            "kannada": "ಉದ್ಯೋಗ ಮತ್ತು ಇಂಟರ್ನ್‌ಶಿಪ್",
            "icon": "bi-briefcase",
            "color": "#4527a0",
            "description": "Public and private job vacancies, apprenticeships, tech internships, and job fairs in Mysuru.",
            "synonyms": ["job", "internship", "career", "recruitment", "kea", "walk-in", "vacancy", "hiring", "ಉದ್ಯೋಗ", "ಕೆಲಸ"]
        },
        "Technology and AI": {
            "slug": "technology",
            "kannada": "ತಂತ್ರಜ್ಞಾನ ಮತ್ತು ಎಐ",
            "icon": "bi-cpu",
            "color": "#283593",
            "description": "Artificial intelligence, software bootcamps, tech hackathons, and Mysuru Beyond Bengaluru innovation.",
            "synonyms": ["technology", "ai", "artificial intelligence", "tech", "coding", "software", "machine learning", "ತಂತ್ರಜ್ಞಾನ", "ಎಐ"]
        },
        "Business and startups": {
            "slug": "business",
            "kannada": "ವ್ಯಾಪಾರ ಮತ್ತು ನವೋದ್ಯಮ",
            "icon": "bi-graph-up-arrow",
            "color": "#c2185b",
            "description": "Startup funding, seed grants, MSME loans, incubation centers, and entrepreneur support.",
            "synonyms": ["business", "startup", "msme", "funding", "entrepreneur", "incubation", "ವ್ಯಾಪಾರ", "ನವೋದ್ಯಮ", "ಉದ್ಯಮ"]
        },
        "Health and public awareness": {
            "slug": "health",
            "kannada": "ಆರೋಗ್ಯ ಮತ್ತು ಸಾರ್ವಜನಿಕ ಜಾಗೃತಿ",
            "icon": "bi-heart-pulse",
            "color": "#c62828",
            "description": "Ayushman Bharat, Tele-MANAS, district health campaigns, vaccination drives, and medical awareness.",
            "synonyms": ["health", "medical", "hospital", "tele-manas", "wellness", "arogya", "ಆರೋಗ್ಯ", "ಆಸ್ಪತ್ರೆ"]
        },
        "Local news and politics": {
            "slug": "local-news",
            "kannada": "ಸ್ಥಳೀಯ ಸುದ್ದಿ ಮತ್ತು ರಾಜಕೀಯ",
            "icon": "bi-megaphone",
            "color": "#4e342e",
            "description": "Mysuru City Corporation civic updates, district administration notices, and regional politics.",
            "synonyms": ["local", "news", "politics", "mcc", "civic", "administration", "ಸ್ಥಳೀಯ ಸುದ್ದಿ", "ರಾಜಕೀಯ"]
        },
        "Weather and environment": {
            "slug": "weather",
            "kannada": "ಹವಾಮಾನ ಮತ್ತು ಪರಿಸರ",
            "icon": "bi-cloud-sun",
            "color": "#00838f",
            "description": "Monsoon forecast, KSNDMC weather alerts, reservoir levels, and Chamundi Hill conservation.",
            "synonyms": ["weather", "environment", "rain", "monsoon", "climate", "ksndmc", "ಹವಾಮಾನ", "ಪರಿಸರ", "ಮಳೆ"]
        },
        "Events, festivals and competitions": {
            "slug": "events",
            "kannada": "ಕಾರ್ಯಕ್ರಮಗಳು, ಹಬ್ಬಗಳು ಮತ್ತು ಸ್ಪರ್ಧೆಗಳು",
            "icon": "bi-calendar-event",
            "color": "#ad1457",
            "description": "Mysuru Dasara, Yuva Sambhrama, state science competitions, and collegiate festivals.",
            "synonyms": ["events", "festivals", "competitions", "dasara", "youth festival", "competition", "ಹಬ್ಬ", "ಸ್ಪರ್ಧೆ", "ಕಾರ್ಯಕ್ರಮ"]
        },
        "Women empowerment and welfare schemes": {
            "slug": "women-welfare",
            "kannada": "ಮಹಿಳಾ ಸಬಲೀಕರಣ ಮತ್ತು ಕಲ್ಯಾಣ ಯೋಜನೆಗಳು",
            "icon": "bi-gender-female",
            "color": "#880e4f",
            "description": "Gruha Lakshmi, Udyogini entrepreneur scheme, women SHG aid, and girl child educational incentives.",
            "synonyms": ["women", "mahila", "gruha lakshmi", "udyogini", "female", "welfare", "ಮಹಿಳಾ", "ಗೃಹಲಕ್ಷ್ಮಿ"]
        },
        "Student opportunities": {
            "slug": "student-opportunities",
            "kannada": "ವಿದ್ಯಾರ್ಥಿ ಅವಕಾಶಗಳು",
            "icon": "bi-backpack",
            "color": "#1976d2",
            "description": "College hackathons, student innovation grants, free bus pass schemes, and youth fellowships.",
            "synonyms": ["student", "college", "youth", "hackathon", "fellowship", "competition", "ವಿದ್ಯಾರ್ಥಿ", "ಕಾಲೇಜು"]
        },
        "Skill development and training": {
            "slug": "skill-development",
            "kannada": "ಕೌಶಲ್ಯ ಅಭಿವೃದ್ಧಿ ಮತ್ತು ತರಬೇತಿ",
            "icon": "bi-tools",
            "color": "#f57c00",
            "description": "District Skill Mission bootcamps, GTTC Mysore technical training, EV and drone workshops.",
            "synonyms": ["skill", "training", "bootcamp", "gttc", "ksdc", "drone", "vocational", "ಕೌಶಲ್ಯ", "ತರಬೇತಿ"]
        },
        "Entertainment and culture": {
            "slug": "culture",
            "kannada": "ಮನರಂಜನೆ ಮತ್ತು ಸಂಸ್ಕೃತಿ",
            "icon": "bi-palette",
            "color": "#6a1b9a",
            "description": "Rangayana Mysuru theatre plays, Kannada Sahitya Sammelana, folk music, and heritage exhibitions.",
            "synonyms": ["entertainment", "culture", "theatre", "drama", "rangayana", "literature", "heritage", "ಸಂಸ್ಕೃತಿ", "ಮನರಂಜನೆ", "ನಾಟಕ"]
        }
    }

    # Available interests for user personalization (includes both core and legacy tags)
    AVAILABLE_INTERESTS = [
        "Agriculture and farming",
        "Sports and tournaments",
        "Education and scholarships",
        "Government schemes and announcements",
        "Jobs and internships",
        "Technology and AI",
        "Business and startups",
        "Health and public awareness",
        "Local news and politics",
        "Weather and environment",
        "Events, festivals and competitions",
        "Women empowerment and welfare schemes",
        "Student opportunities",
        "Skill development and training",
        "Entertainment and culture",
        # Legacy aliases for smooth backward compatibility
        "Scholarships",
        "Government schemes",
        "Internships",
        "Jobs",
        "College events",
        "Skill development",
        "Farming",
        "Sports"
    ]

    # Category Canonical Mapping (maps legacy or short category to core category)
    CATEGORY_CANONICAL_MAP = {
        "scholarships": "Education and scholarships",
        "education updates": "Education and scholarships",
        "education": "Education and scholarships",
        "government schemes": "Government schemes and announcements",
        "government rules": "Government schemes and announcements",
        "government": "Government schemes and announcements",
        "internships": "Jobs and internships",
        "jobs": "Jobs and internships",
        "skill development": "Skill development and training",
        "college events": "Events, festivals and competitions",
        "farming": "Agriculture and farming",
        "agriculture": "Agriculture and farming",
        "sports": "Sports and tournaments",
        "technology and science": "Technology and AI",
        "technology": "Technology and AI",
        "local and community": "Local news and politics",
        "local news": "Local news and politics",
        "politics": "Local news and politics",
        "business and economy": "Business and startups",
        "business": "Business and startups",
    }
    
    # Multilingual Support (6 languages)
    AVAILABLE_LANGUAGES = [
        "English",
        "Kannada",
        "Telugu",
        "Tamil",
        "Malayalam",
        "Hindi"
    ]
    
    LANGUAGE_CODES = {
        "English": "en-IN",
        "Kannada": "kn-IN",
        "Telugu": "te-IN",
        "Tamil": "ta-IN",
        "Malayalam": "ml-IN",
        "Hindi": "hi-IN"
    }

    LANGUAGE_NATIVE_NAMES = {
        "English": "English",
        "Kannada": "ಕನ್ನಡ",
        "Telugu": "తెలుగు",
        "Tamil": "தமிழ்",
        "Malayalam": "മലയാളം",
        "Hindi": "हिन्दी"
    }

    NEWS_CATEGORIES = [
        "Sports",
        "Agriculture",
        "Government Rules",
        "Politics",
        "Education",
        "Technology and Science",
        "Local and Community",
        "Business and Economy"
    ]

    # slug, database category, nav label key, icon
    NEWS_SECTIONS = [
        ("sports", "Sports", "sports", "bi-trophy"),
        ("farming", "Agriculture", "farming", "bi-moisture"),
        ("government", "Government Rules", "government", "bi-bank"),
        ("politics", "Politics", "politics", "bi-megaphone"),
        ("education", "Education", "education", "bi-mortarboard"),
        ("technology", "Technology and Science", "technology", "bi-cpu"),
        ("local", "Local and Community", "local", "bi-geo-alt"),
        ("business", "Business and Economy", "business", "bi-graph-up"),
    ]

    SPORTS_SUBCATEGORIES = [
        "Cricket",
        "Football",
        "Badminton",
        "Hockey",
        "Kabaddi",
        "Athletics",
        "Olympics",
        "Other sports"
    ]

    # Public RSS feeds. Refresh is manual unless SUNOLOCAL_AUTO_REFRESH=1.
    # PIB press releases are official government notices, not scraped article pages.
    RSS_FEEDS = [
        {
            "name": "Press Information Bureau",
            "url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
            "category": "Government Rules",
            "subcategory": "Central announcements",
            "location": "All India",
            "source_class": "official",
            "is_official_government": 1,
        }
    ]
    
    EDUCATION_LEVELS = [
        "Undergraduate (PUC / Diploma / Degree)",
        "Postgraduate (Master's / Ph.D.)",
        "Engineering / Tech Student",
        "Job Seeker / Recent Graduate",
        "High School Student"
    ]
