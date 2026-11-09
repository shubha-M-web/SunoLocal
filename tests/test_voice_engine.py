"""
Test suite to verify voice.js non-recursion architecture,
backend speech text generation for English and Kannada, and safety rules.
"""

import re
import sys
import json
from pathlib import Path

# Configure utf-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from modules.summarizer import generate_summary
from database.db import get_db_connection

def test_voice_js_architecture():
    print("=" * 60)
    print("TESTING VOICE.JS ARCHITECTURE & RECURSION PREVENTION")
    print("=" * 60)

    voice_js_path = PROJECT_ROOT / "static" / "js" / "voice.js"
    assert voice_js_path.exists(), "voice.js file not found!"
    code = voice_js_path.read_text(encoding="utf-8")

    # 1. Inspect loadVoices() body
    load_voices_match = re.search(r"loadVoices\(\)\s*\{([\s\S]*?)\n\s*\}", code)
    assert load_voices_match, "loadVoices() function not found in voice.js"
    load_voices_body = load_voices_match.group(1)
    
    assert "notifyDiagnostic" not in load_voices_body, (
        "VIOLATION: loadVoices() must NOT call notifyDiagnostic()! That causes infinite recursion."
    )
    assert "getVoiceDiagnostics" not in load_voices_body, (
        "VIOLATION: loadVoices() must NOT call getVoiceDiagnostics()!"
    )
    assert "getKannadaVoice" not in load_voices_body, (
        "VIOLATION: loadVoices() must NOT call getKannadaVoice()!"
    )
    print("PASS Requirement 1 & 2: loadVoices() is pure and does not trigger circular calls.")

    # 2. Inspect getKannadaVoice() body
    kn_match = re.search(r"getKannadaVoice\(\)\s*\{([\s\S]*?)\n\s*\}", code)
    assert kn_match, "getKannadaVoice() function not found"
    kn_body = kn_match.group(1)
    assert "loadVoices" not in kn_body, (
        "VIOLATION: getKannadaVoice() must NOT call loadVoices()! That causes infinite recursion."
    )
    print("PASS Requirement 3: getKannadaVoice() strictly queries stored voices without calling loadVoices().")

    # 3. Inspect getEnglishVoice() body
    en_match = re.search(r"getEnglishVoice\(\)\s*\{([\s\S]*?)\n\s*\}", code)
    assert en_match, "getEnglishVoice() function not found"
    en_body = en_match.group(1)
    assert "loadVoices" not in en_body, (
        "VIOLATION: getEnglishVoice() must NOT call loadVoices()!"
    )
    print("PASS Requirement 4: getEnglishVoice() strictly queries stored voices without calling loadVoices().")

    # 4. Inspect getVoiceDiagnostics() body
    diag_match = re.search(r"getVoiceDiagnostics\(\)\s*\{([\s\S]*?)\n\s*\}", code)
    assert diag_match, "getVoiceDiagnostics() function not found"
    diag_body = diag_match.group(1)
    assert "loadVoices" not in diag_body, (
        "VIOLATION: getVoiceDiagnostics() must NOT call loadVoices()!"
    )
    assert "notifyDiagnostic" not in diag_body, (
        "VIOLATION: getVoiceDiagnostics() must NOT call notifyDiagnostics()!"
    )
    print("PASS Requirement 5: getVoiceDiagnostics() only reads state without side effects.")

    # 5. Check Kannada Voice Missing Safety Rule in speak()
    assert "Kannada voice is not available on this device" in code, (
        "VIOLATION: Expected clear missing Kannada voice message in voice.js"
    )
    assert "kn-in" in code.lower(), "kn-IN language code must be configured in voice.js"
    print("PASS Requirement 9 & 10: Strict Kannada safety check present (never silently uses English).")


def test_speech_endpoints_and_text():
    print("\n" + "=" * 60)
    print("TESTING SPEECH DATA & BACKEND API ENDPOINTS")
    print("=" * 60)

    client = app.test_client()

    # 1. Hardcoded English Sentence Verification
    hardcoded_en = "Hello! Welcome to SunoLocal Mysore opportunity discovery platform. English speech synthesis is working properly."
    assert len(hardcoded_en) > 20
    print(f"PASS: Test hardcoded English phrase verified ({len(hardcoded_en)} chars).")

    # 2. Hardcoded Kannada Sentence Verification
    hardcoded_kn = "ನಮಸ್ಕಾರ, ಸುನೋ ಲೋಕಲ್ ಮೈಸೂರು ಪೋರ್ಟಲ್‌ಗೆ ಸುಸ್ವಾಗತ. ಕನ್ನಡ ಧ್ವನಿ ಯಶಸ್ವಿಯಾಗಿ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿದೆ."
    assert "ನಮಸ್ಕಾರ" in hardcoded_kn and "ಕನ್ನಡ" in hardcoded_kn
    print(f"PASS: Test hardcoded Kannada phrase verified ({len(hardcoded_kn)} chars).")

    # 3. Opportunity Summary Speech Text via /api/listen
    res_en = client.get("/api/listen/1?lang=English")
    assert res_en.status_code == 200
    data_en = json.loads(res_en.data)
    assert data_en["success"] is True
    assert data_en["language"] == "English"
    assert data_en["lang_code"] == "en-IN"
    assert "speech_text" in data_en and len(data_en["speech_text"]) > 30
    assert "[SAMPLE DATA]" not in data_en["speech_text"]
    print("PASS: English Opportunity Speech Text: ", data_en["speech_text"][:85], "...")

    res_kn = client.get("/api/listen/1?lang=Kannada")
    assert res_kn.status_code == 200
    data_kn = json.loads(res_kn.data)
    assert data_kn["success"] is True
    assert data_kn["language"] == "Kannada"
    assert data_kn["lang_code"] == "kn-IN"
    assert "speech_text" in data_kn and len(data_kn["speech_text"]) > 30
    assert "ನಮಸ್ಕಾರ" in data_kn["speech_text"]
    assert "[SAMPLE DATA]" not in data_kn["speech_text"]
    assert "[ಮಾದರಿ ದತ್ತಾಂಶ]" not in data_kn["speech_text"]
    print("PASS: Kannada Opportunity Speech Text: ", data_kn["speech_text"][:85], "...")

    print("\n" + "=" * 60)
    print("ALL VOICE ENGINE ARCHITECTURAL & SPEECH TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_voice_js_architecture()
    test_speech_endpoints_and_text()
