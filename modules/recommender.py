"""
Intelligent Recommendation Engine for SunoLocal.
Uses a transparent, weighted multi-factor scoring algorithm:
- Category & Interest Alignment (50%)
- Geographic Proximity / Location Relevance (30%)
- Opportunity Timeliness & Urgency (20%)

Transparently provides match scores and human-readable explanations.
Designed modularly so TF-IDF/embeddings can be plugged in seamlessly.
"""

from datetime import datetime, date
from config import Config

def calculate_match_score(opportunity, preferences):
    """
    Computes a transparent 0-100 match score and explanation.
    
    Args:
        opportunity: dict or sqlite3.Row of the opportunity.
        preferences: dict containing:
            - location: str (e.g., 'Mysuru')
            - interests: list of str (e.g., ['Scholarships', 'Internships'])
            - education_level: str
    
    Returns:
        dict with:
            - score: int (0 to 100)
            - factors: dict breakdown
            - explanation: str human-friendly explanation
            - badge_class: str CSS class for UI
    """
    opp = dict(opportunity) if not isinstance(opportunity, dict) else opportunity
    prefs = dict(preferences) if not isinstance(preferences, dict) else preferences

    user_location = (prefs.get("location") or "Mysuru").strip().lower()
    user_interests = [i.strip().lower() for i in prefs.get("interests", [])]
    
    opp_category = (opp.get("category") or "").strip().lower()
    opp_location = (opp.get("location") or "").strip().lower()
    opp_title = (opp.get("title") or "").lower()
    opp_desc = (opp.get("short_description") or "").lower()
    opp_deadline = opp.get("deadline")

    interest_score = 0
    location_score = 0
    timeliness_score = 0
    explanation_parts = []

    # 1. Category & Interest Match (Max 50 points)
    direct_match = False
    matched_label = opp.get("category")

    for interest in user_interests:
        canon_user = Config.CATEGORY_CANONICAL_MAP.get(interest, interest).lower()
        canon_opp = Config.CATEGORY_CANONICAL_MAP.get(opp_category, opp_category).lower()
        if (opp_category == interest or
            canon_user == canon_opp or
            interest in opp_category or
            opp_category in interest):
            direct_match = True
            matched_label = opp.get('category')
            break

    if direct_match:
        interest_score = 40
        explanation_parts.append(f"Directly matches your interest in '{matched_label}'")
    else:
        # Check partial keyword match in user interests vs category
        matched_interest = None
        for interest in user_interests:
            if interest in opp_title or interest in opp_desc:
                matched_interest = interest
                break
        if matched_interest:
            interest_score = 25
            explanation_parts.append(f"Content relates to your interest in '{matched_interest.capitalize()}'")
        else:
            interest_score = 5

    # 2. Location Match (Max 30 points)
    if opp_location == user_location:
        location_score = 30
        explanation_parts.append(f"Located directly in {opp.get('location')}")
    elif "karnataka" in opp_location or opp_location in ["other karnataka", "statewide", "all karnataka"]:
        location_score = 20
        explanation_parts.append("Available state-wide across Karnataka")
    elif user_location == "mysuru" and opp_location == "mandya":
        location_score = 22
        explanation_parts.append("In neighboring Mandya district (commutable from Mysuru)")
    elif user_location == "mysuru" and opp_location == "bengaluru":
        location_score = 15
        explanation_parts.append("Bengaluru opportunity accessible to Mysuru students")
    elif opp_location == "all india" or "online" in opp_desc:
        location_score = 18
        explanation_parts.append("Online / Pan-India opportunity")
    else:
        location_score = 8

    # 3. Timeliness & Deadline Status (Max 20 points)
    if opp_deadline:
        try:
            deadline_date = datetime.strptime(opp_deadline.strip(), "%Y-%m-%d").date()
            today = date.today()
            delta = (deadline_date - today).days

            if delta < 0:
                timeliness_score = 2
                explanation_parts.append("Notice: Application deadline has passed")
            elif delta <= 7:
                timeliness_score = 20
                explanation_parts.append(f"Closing soon ({delta} days left)")
            elif delta <= 30:
                timeliness_score = 18
                explanation_parts.append(f"Active application window ({delta} days remaining)")
            else:
                timeliness_score = 14
                explanation_parts.append("Active opportunity with open deadline")
        except ValueError:
            timeliness_score = 10
    else:
        timeliness_score = 12
        explanation_parts.append("Ongoing / rolling deadline")

    total_score = min(100, max(0, interest_score + location_score + timeliness_score))

    # Badge formatting
    if total_score >= 80:
        badge_class = "match-high"
    elif total_score >= 50:
        badge_class = "match-medium"
    else:
        badge_class = "match-low"

    explanation = "; ".join(explanation_parts) if explanation_parts else "General student opportunity."

    return {
        "score": total_score,
        "interest_score": interest_score,
        "location_score": location_score,
        "timeliness_score": timeliness_score,
        "explanation": explanation,
        "badge_class": badge_class
    }


def rank_opportunities(opportunities, preferences, sort_by="relevance"):
    """
    Enriches a list of opportunities with recommendation scores and sorts them.
    
    Args:
        opportunities: list of opportunity dicts/rows
        preferences: user preference dict
        sort_by: 'relevance', 'deadline', or 'recent'
    
    Returns:
        Sorted list of dicts with match information attached.
    """
    enriched = []
    for item in opportunities:
        # Convert sqlite3.Row to dict if needed
        data = dict(item) if not isinstance(item, dict) else item.copy()
        match_info = calculate_match_score(data, preferences)
        data["match_score"] = match_info["score"]
        data["match_explanation"] = match_info["explanation"]
        data["match_badge_class"] = match_info["badge_class"]
        data["factors"] = {
            "interest": match_info["interest_score"],
            "location": match_info["location_score"],
            "timeliness": match_info["timeliness_score"]
        }
        enriched.append(data)

    if sort_by == "relevance":
        enriched.sort(key=lambda x: x["match_score"], reverse=True)
    elif sort_by == "deadline":
        # Sort by upcoming deadline (None or past dates at the end)
        def deadline_key(x):
            d = x.get("deadline")
            if not d:
                return "9999-12-31"
            return d
        enriched.sort(key=deadline_key)
    elif sort_by == "recent":
        enriched.sort(key=lambda x: x.get("publication_date") or "", reverse=True)

    return enriched
