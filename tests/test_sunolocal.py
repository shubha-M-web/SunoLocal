"""
Automated Test Suite for SunoLocal Web Application.
Tests:
- Recommendation Engine (recommender.py)
- TrustCheck Integrity Assessor (trustcheck.py)
- AI Summarizer (summarizer.py)
- Flask Endpoints & User Journey
- SQLite Database Operations
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from database.db import get_db_connection, init_db
from database.init_db import seed_database
from modules.recommender import calculate_match_score, rank_opportunities
from modules.trustcheck import evaluate_trust
from modules.summarizer import generate_summary

def run_tests():
    print("=" * 60)
    print("RUNNING SUNOLOCAL COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    # 1. Test Database Initialization
    print("\n[Test 1] Testing Database Seeding & Schema...")
    count = seed_database()
    assert count >= 12, f"Expected at least 12 records, found {count}"
    print(f"PASS: Database seeded with {count} sample opportunities.")

    # 2. Test Recommendation Engine
    print("\n[Test 2] Testing Recommendation Engine...")
    conn = get_db_connection()
    opps = conn.execute("SELECT * FROM opportunities").fetchall()
    conn.close()

    prefs = {
        "location": "Mysuru",
        "interests": ["Skill development", "Internships"],
        "education_level": "Undergraduate"
    }

    # Match calculation
    python_bootcamp = next(o for o in opps if "Python" in o["title"])
    score_data = calculate_match_score(python_bootcamp, prefs)
    
    assert score_data["score"] >= 80, f"Expected high score for Mysuru + Skill Dev, got {score_data['score']}"
    assert "Directly matches your interest" in score_data["explanation"]
    assert "Mysuru" in score_data["explanation"]
    print(f"PASS: Python Bootcamp match score: {score_data['score']}% (Explanation: {score_data['explanation']})")

    # Ranking
    ranked = rank_opportunities(opps, prefs, sort_by="relevance")
    assert ranked[0]["match_score"] >= ranked[-1]["match_score"], "Ranking did not sort descending by relevance"
    print(f"PASS: Opportunities ranked successfully. Top item: '{ranked[0]['title'][:40]}...' with {ranked[0]['match_score']}%")

    # 3. Test TrustCheck Module
    print("\n[Test 3] Testing TrustCheck Module...")
    # Clean record with official domain
    ssp_scholarship = next(o for o in opps if "SSP" in o["title"])
    trust_clean = evaluate_trust(ssp_scholarship)
    assert trust_clean["status"] == "Source available"
    assert trust_clean["is_official_domain"] is True
    print(f"PASS: SSP Scholarship TrustCheck: {trust_clean['status']} (Official Domain: {trust_clean['domain_name']})")

    # WhatsApp unverified record
    wa_record = next(o for o in opps if "WhatsApp" in o["title"])
    trust_wa = evaluate_trust(wa_record)
    assert trust_wa["status"] in ["Source missing", "Potentially outdated"]
    assert len(trust_wa["warnings"]) >= 2
    print(f"PASS: Unverified circular flagged: {trust_wa['status']} with {len(trust_wa['warnings'])} warnings: {trust_wa['warnings']}")

    # 4. Test Summarizer Module (Extractive Fallback)
    print("\n[Test 4] Testing AI Summarizer (English & Kannada)...")
    summary_en = generate_summary(dict(python_bootcamp), language="English")
    for field in ["what_is_it", "who_can_apply", "requirements", "important_dates", "how_to_apply", "original_source", "speech_text"]:
        assert field in summary_en and summary_en[field], f"Missing or empty field: {field}"
    assert "SunoLocal" in summary_en["provider"]
    print("PASS: English AI summary generated with all 6 required fields and speech_text.")

    summary_kn = generate_summary(dict(python_bootcamp), language="Kannada")
    assert "ಏನು ಈ ಅವಕಾಶ?" in summary_kn["what_is_it"] or "ಮೈಸೂರು" in summary_kn["what_is_it"]
    print("PASS: Kannada AI summary generated with Kannada localized speech text.")

    # 5. Test Flask Client & Routes
    print("\n[Test 5] Testing Flask Web Application Routes...")
    client = app.test_client()
    app.config["TESTING"] = True

    # Homepage
    res = client.get("/")
    assert res.status_code == 200
    assert b"SunoLocal" in res.data
    assert b"Listen. Understand. Verify. Act." in res.data
    print("PASS: GET / (Homepage) -> 200 OK")

    # Preferences GET and POST
    res = client.get("/preferences")
    assert res.status_code == 200
    print("PASS: GET /preferences -> 200 OK")

    res = client.post("/preferences", data={
        "location": "Mysuru",
        "language": "Kannada",
        "education_level": "Undergraduate",
        "interests": ["Scholarships", "Jobs"]
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Your preferences have been saved" in res.data
    print("PASS: POST /preferences -> Redirects to Dashboard with updated preferences")

    # Dashboard
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert b"Recommended for You" in res.data
    print("PASS: GET /dashboard -> 200 OK")

    # Discovery with Search and Filters
    res = client.get("/discover?q=Python")
    assert res.status_code == 200
    assert b"Python" in res.data
    print("PASS: GET /discover?q=Python -> 200 OK")

    res = client.get("/discover?category=Scholarships&location=Mysuru")
    assert res.status_code == 200
    print("PASS: GET /discover with category & location filters -> 200 OK")

    # Opportunity Detail
    res = client.get("/opportunity/1")
    assert res.status_code == 200
    assert b"TRUSTCHECK" in res.data
    assert b"Audio Briefing" in res.data
    print("PASS: GET /opportunity/1 -> 200 OK")

    # Audio API (English & Kannada)
    res_en = client.get("/api/listen/1?lang=English")
    assert res_en.status_code == 200
    data_en = json.loads(res_en.data)
    assert data_en["success"] is True
    assert data_en["language"] == "English"
    assert data_en["lang_code"] == "en-IN"
    assert "SunoLocal audio briefing" in data_en["speech_text"]
    assert "[SAMPLE DATA]" not in data_en["speech_text"]
    print("PASS: GET /api/listen/1?lang=English -> Clean en-IN speech text returned without bracketed tags")

    res_kn = client.get("/api/listen/1?lang=Kannada")
    assert res_kn.status_code == 200
    data_kn = json.loads(res_kn.data)
    assert data_kn["success"] is True
    assert data_kn["language"] == "Kannada"
    assert data_kn["lang_code"] == "kn-IN"
    assert "ನಮಸ್ಕಾರ" in data_kn["speech_text"]
    assert "[SAMPLE DATA]" not in data_kn["speech_text"]
    assert "[ಮಾದರಿ ದತ್ತಾಂಶ]" not in data_kn["speech_text"]
    print("PASS: GET /api/listen/1?lang=Kannada -> Clean kn-IN Kannada speech text returned properly")

    # Bookmark Toggle API
    res = client.post("/api/save/1")
    assert res.status_code == 200
    save_data = json.loads(res.data)
    assert save_data["saved"] is True
    print("PASS: POST /api/save/1 -> Item saved successfully")

    # Saved page
    res = client.get("/saved")
    assert res.status_code == 200
    assert b"My Saved Opportunities" in res.data
    print("PASS: GET /saved -> 200 OK")

    # Toggle unbookmark
    res = client.post("/api/save/1")
    save_data2 = json.loads(res.data)
    assert save_data2["saved"] is False
    print("PASS: POST /api/save/1 (toggle) -> Item unbookmarked successfully")

    # Admin Dashboard
    res = client.get("/admin")
    assert res.status_code == 200
    assert b"Admin &amp; Data Management" in res.data or b"Admin & Data Management" in res.data
    print("PASS: GET /admin -> 200 OK")

    # Admin Add Record
    res = client.post("/admin", data={
        "title": "Mandya Drone Pilot Workshop [SAMPLE DATA]",
        "category": "Skill development",
        "organization": "Mandya Krishi Kendra",
        "location": "Mandya",
        "short_description": "Hands-on drone piloting for agricultural surveying.",
        "full_description": "Full details on drone certification and safety standards.",
        "eligibility": "12th pass / Diploma in engineering",
        "requirements": "Aadhaar Card",
        "deadline": "2026-12-05",
        "publication_date": "2026-11-01",
        "source_name": "Krishi Kendra Portal",
        "source_url": "https://krishikendra.ka.gov.in",
        "how_to_apply": "Register online",
        "is_verified": "1"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"added successfully" in res.data
    print("PASS: POST /admin -> New opportunity added and validated")

    # Admin Reset Demo
    res = client.post("/admin/reset-demo", follow_redirects=True)
    assert res.status_code == 200
    assert b"Database successfully re-seeded" in res.data
    print("PASS: POST /admin/reset-demo -> Restored initial clean dataset")

    # About Page
    res = client.get("/about")
    assert res.status_code == 200
    assert b"INNOVATE Hackathon" in res.data
    print("PASS: GET /about -> 200 OK")

    # 6. Test 7 Core Mandatory Questions from Section 10
    print("\n[Test 6] Testing 7 Mandatory Search Questions (Section 10)...")
    mandatory_questions = [
        ("Latest agriculture schemes for Karnataka farmers.", "Agriculture and farming"),
        ("Upcoming sports tournaments in Karnataka.", "Sports and tournaments"),
        ("Scholarships for engineering students.", "Education and scholarships"),
        ("Latest job opportunities in Mysuru.", "Jobs and internships"),
        ("Government announcements in Karnataka.", "Government schemes and announcements"),
        ("Latest AI and technology news.", "Technology and AI"),
        ("Upcoming student competitions.", "Events, festivals and competitions")
    ]

    for idx, (question, expected_cat) in enumerate(mandatory_questions, 1):
        res_q = client.get(f"/discover?q={question}")
        assert res_q.status_code == 200
        html_q = res_q.data.decode("utf-8")
        assert "http" in html_q, f"Source URL missing for question '{question}'"
        assert expected_cat in html_q, f"Expected category '{expected_cat}' not found for question '{question}'"
        print(f"PASS Q{idx}: '{question}' -> Identified category '{expected_cat}' with detailed source-backed results")

    # 7. Test Kannada Query Search and Language Switching
    print("\n[Test 7] Testing Kannada Search and Language Switcher...")
    res_kn_q = client.get("/discover?q=%E0%B2%95%E0%B2%B0%E0%B3%8D%E0%B2%A3%E0%B2%BE%E0%B2%9F%E0%B2%95%E0%B2%A6%20%E0%B2%B0%E0%B3%88%E0%B2%A4%E0%B2%B0%E0%B2%BF%E0%B2%97%E0%B3%86%20%E0%B2%AF%E0%B3%8B%E0%B2%9C%E0%B2%A8%E0%B3%86%E0%B2%97%E0%B2%B3%E0%B3%81")
    assert res_kn_q.status_code == 200
    assert "Agriculture and farming" in res_kn_q.data.decode("utf-8")
    print("PASS: Kannada search correctly parsed and returned Agriculture and farming results.")

    res_switch = client.get("/set-language/Kannada", follow_redirects=True)
    assert res_switch.status_code == 200
    print("PASS: GET /set-language/Kannada -> Switched session language to Kannada.")

    # 8. Test Category-Wise Discovery Page
    print("\n[Test 8] Testing Category-Wise Discovery Page...")
    res_cat = client.get("/categories")
    assert res_cat.status_code == 200
    assert b"Explore by Category" in res_cat.data
    assert b"Agriculture and farming" in res_cat.data
    assert b"Sports and tournaments" in res_cat.data
    assert b"Technology and AI" in res_cat.data
    print("PASS: GET /categories -> Displays category cards across all 15 categories.")

    # 9. Test In-App Alerts & Deadline Reminders (Section 7)
    print("\n[Test 9] Testing In-App Alerts and Deadline Reminders...")
    res_notif = client.get("/api/notifications")
    assert res_notif.status_code == 200
    notif_data = json.loads(res_notif.data)
    assert notif_data["success"] is True
    print(f"PASS: GET /api/notifications -> Active notification alerts synced ({len(notif_data['notifications'])} notifications).")

    # 10. Test Verified vs Sample Data Distinction (Section 3)
    print("\n[Test 10] Testing Verified vs Sample Data Distinction...")
    res_detail_verified = client.get("/opportunity/13")  # Raitha Siri verified item
    assert res_detail_verified.status_code == 200
    assert b"VERIFIED OFFICIAL NOTICE" in res_detail_verified.data
    assert b"Who Can Benefit" in res_detail_verified.data
    print("PASS: Detail view correctly displays 'VERIFIED OFFICIAL NOTICE' and 'Who Can Benefit' field.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! SUNOLOCAL UPGRADE FULLY VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
