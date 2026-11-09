# SunoLocal 🎙️📍

> **Tagline:** *Listen. Understand. Verify. Act.*  
> **Built for:** INNOVATE Hackathon  
> **Target Audience:** College students, job seekers, internship seekers, scholarship applicants  
> **Primary Location:** Mysuru, Karnataka, India (expanding to Mandya, Bengaluru, and Statewide)  
> **Languages:** English and Kannada

---

## 🌟 Concept & Problem Overview

Important local educational opportunities—state scholarships (SSP), district skill bootcamps, KDEM startup apprenticeships, CSIR research projects, and government welfare schemes—are scattered across dozens of disconnected departmental websites and dense PDF circulars. 

Students often:
1. **Miss tight deadlines** because information is fragmented.
2. **Struggle to understand bureaucratic language and legalistic eligibility criteria.**
3. **Fall victim to fake WhatsApp forwards** advertising fake jobs or unauthorized spot application fees.
4. **Lack accessible audio channels** when reading complex notifications on mobile devices.

### 💡 The SunoLocal Solution
SunoLocal provides a single, personalized platform following a clean 6-step human-centered workflow:
**PERSONALIZE → DISCOVER → UNDERSTAND → VERIFY → LISTEN → ACT**

---

## 🛠️ Technology Stack

- **Frontend:** HTML5, CSS3 (Modern SaaS design system, responsive card grids), JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Web Speech API (Client-Side Text-to-Speech).
- **Backend:** Python 3.12, Flask 3.1.
- **Database:** SQLite 3 with parameterized queries, relational schema (`users`, `user_preferences`, `opportunities`, `saved_opportunities`, `recently_viewed`).
- **Intelligence Modules:**
  - `recommender.py`: Multi-factor transparent scoring engine (Category & Interest Alignment 50%, Geographic Proximity 30%, Urgency & Deadline 20%).
  - `summarizer.py`: Configurable LLM API (Google Gemini / OpenAI compatible) with an offline, zero-hallucination Extractive Fallback Engine that structures circulars into 6 concise questions in English and Kannada.
  - `trustcheck.py`: Domain security audit (detects `.gov.in`, `.ac.in`, `.res.in`), expiration calculation, missing source warnings, and safety disclaimers.

---

## 🚀 Quickstart Guide for Windows

### 1. Prerequisites
Ensure Python 3.10+ is installed on your Windows machine.
Check by opening PowerShell or Command Prompt:
```powershell
python --version
```

### 2. Navigate to the Project Directory
```powershell
cd C:\Users\shubh\.gemini\antigravity\scratch\SunoLocal
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Initialize Database with Sample Data
```powershell
python database/init_db.py
```

### 5. Run the Application
```powershell
python app.py
```

### 6. Open in Your Browser
Open: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧭 The 6 Core Features Implemented

| Feature | Implementation | How to Test |
| :--- | :--- | :--- |
| **1. Personalization** | Stores location (Mysuru, Mandya, Bengaluru), education level, language (English/Kannada), and multi-select interests in SQLite. | Visit `/preferences`, change your district to Mysuru and interests to Skill Development. |
| **2. Smart Discovery** | Multi-criteria search, category filters, location filters, trust status filters, and sorting by relevance or deadline. | Visit `/discover`, type "Python" or filter by "Mysuru". |
| **3. Recommendation Engine** | Transparent 0–100 weighted scoring with human-readable match explanations (no black-box claims). | View match badges (e.g. `94% Match`) and hover to see the transparent score breakdown. |
| **4. AI Summarization** | 6-part structured breakdown (What, Who, Requirements, Dates, How to Apply, Source). Works with Gemini API or offline Extractive Fallback. | Open any opportunity (e.g. SSP Scholarship) to see the structured breakdown. |
| **5. TrustCheck** | Analyzes source links, checks official domain status (`.gov.in`, `.ac.in`), calculates days to deadline, flags missing data. | Inspect the sample WhatsApp forward record to see "Source Missing" and "Potentially Outdated" warning flags. |
| **6. Listen (Voice TTS)** | Web Speech API text-to-speech with English & Kannada voice detection, play/pause/resume/stop controls, speed adjustment, floating dock, and Voice Diagnostics. | Click "EN" or "KN" on any card or open the Voice Diagnostics modal. |
| **7. Voice Diagnostics** | Live inspection of browser voices, `kn-IN` voice availability, and Windows/Edge/Chrome setup guide. | Click the "Voice Diagnostic 🎙️" button in the navbar. |
| **8. User Hub / Dashboard** | Personalized welcome, metric counters, recommended feed, upcoming deadlines, recently viewed, and saved items. | Visit `/dashboard` to view your personalized control center. |
| **9. Admin Management** | Form with input validation to add, edit, or delete opportunities, plus a 1-click "Reset Sample Data" button. | Visit `/admin` to add or modify records. |

---

## 🔊 How to Enable Kannada (kn-IN) Voice on Windows, Edge, and Chrome

### 1. Microsoft Edge (Recommended — No Installation Required)
Open SunoLocal in **Microsoft Edge**. Edge includes built-in online Natural voices for Indian languages including:
- `Microsoft Gagan Online (Natural) - Kannada (India)` (`kn-IN`)
- `Microsoft Sapna Online (Natural) - Kannada (India)` (`kn-IN`)

No extra download is needed; Edge streams high-definition Kannada speech directly through the browser Web Speech API.

### 2. Windows 10 & 11 (For Offline & Chrome Support)
1. Open Windows **Settings** (`Win + I`) &rarr; navigate to **Time & Language** &rarr; **Language & Region**.
2. Click **Add a language** &rarr; Search for **Kannada (ಕನ್ನಡ)**.
3. In the install dialog, make sure **Text-to-speech** (or *Speech*) is checked.
4. Click **Install**.
5. Once downloaded, restart your browser (Google Chrome or Edge).
6. Click **Voice Diagnostic** in the SunoLocal navbar to verify the voice is detected.

### 3. Strict Safety Rule for Kannada Speech
If a user selects Kannada and no `kn-IN` voice is present on the client device:
- SunoLocal **never silently falls back to an English voice** (which would produce silence or broken noise).
- SunoLocal displays the clear message:
  > *"Kannada voice is not available on this device. Please install a Kannada speech voice or use a supported browser."*
- SunoLocal provides the full localized Kannada transcript so the student can read along seamlessly.

---

## 🎙️ Instructions for Recording a 3-Minute Hackathon Demo

- **Minute 0:00 - 0:45 (The Problem & Personalization):**
  - Show the homepage headline and explain the real problem in Mysuru & Karnataka: scattered notices and fake WhatsApp forwards.
  - Click **"Personalize My Feed"**. Select **Mysuru**, choose **Skill Development** & **Internships**, pick **Kannada** or **English**. Click Save.
- **Minute 0:45 - 1:45 (Personalized Discovery & Audio):**
  - Land on the **My Student Hub** (`/dashboard`). Show how the **Mysuru District Skill Development Mission (Python Bootcamp)** is ranked #1 with a **94% Match** because of your Mysuru location.
  - Click **"Listen"** on the card. Point out the floating audio player dock and show the audio briefing playing via browser text-to-speech.
- **Minute 1:45 - 2:30 (Understand & TrustCheck):**
  - Open the **Opportunity Detail** page. Show the 6-question simplified AI summary.
  - Highlight the **TrustCheck panel**: point out how it verified the `skillconnect.ka.gov.in` official government domain and calculated the remaining deadline days.
  - Switch to the **Sample WhatsApp Circular** to demonstrate TrustCheck catching an unverified claim, displaying red warning alerts, and preventing student deception.
- **Minute 2:30 - 3:00 (Admin & Impact):**
  - Open `/admin`, demonstrate adding or modifying a record with safe validation.
  - Conclude with the social impact: empowering first-generation college students and job seekers across Karnataka.

---

## 🔒 Safety and Demo Notice
All demonstration records in this repository are marked with `[SAMPLE DATA]` to ensure absolute transparency. No real student data is collected or transmitted.
