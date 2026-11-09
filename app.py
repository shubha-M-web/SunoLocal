import os
import json
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, g
)

from config import Config
from database.db import get_db_connection, init_db
from database.seed_data import SAMPLE_OPPORTUNITIES
from database.init_db import seed_database
from modules.recommender import calculate_match_score, rank_opportunities
from modules.summarizer import generate_summary
from modules.trustcheck import evaluate_trust
from modules.query_parser import parse_user_query

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database exists on app startup
with app.app_context():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM opportunities")
        count = cur.fetchone()[0]
        if count == 0:
            print("[SunoLocal Startup] Seeding database with initial sample data...")
            seed_database()
    except Exception as e:
        print("[SunoLocal Startup] Initializing fresh database schema...", e)
        seed_database()
    finally:
        conn.close()


def get_current_user_preferences():
    """Fetches user preferences from DB or session, or provides default."""
    user_id = session.get("user_id", 1)
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    active_lang = session.get("language")

    if row:
        row_keys = row.keys()
        try:
            interests = json.loads(row["interests"])
        except Exception:
            interests = ["Scholarships", "Internships", "Skill development"]
        
        pref_lang = active_lang or row["language"] or Config.DEFAULT_LANGUAGE
        return {
            "user_id": user_id,
            "location": row["location"],
            "language": pref_lang,
            "interests": interests,
            "education_level": row["education_level"],
            "user_type": row["user_type"] if "user_type" in row_keys else "student",
            "state": row["state"] if "state" in row_keys else "Karnataka"
        }
    
    # Fallback default preferences
    return {
        "user_id": 1,
        "location": Config.DEFAULT_LOCATION,
        "language": active_lang or Config.DEFAULT_LANGUAGE,
        "interests": ["Scholarships", "Internships", "Skill development"],
        "education_level": "Undergraduate (PUC / Diploma / Degree)",
        "user_type": "student",
        "state": "Karnataka"
    }


def get_user_saved_ids(user_id=1):
    """Returns set of opportunity IDs saved by current user."""
    conn = get_db_connection()
    rows = conn.execute("SELECT opportunity_id FROM saved_opportunities WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return set(r["opportunity_id"] for r in rows)


def sync_user_notifications(user_id=1):
    """Generates authentic notifications for active deadlines and user interest matches."""
    prefs = get_current_user_preferences()
    conn = get_db_connection()
    
    # 1. Real upcoming deadline reminders for saved items (within 35 days)
    saved_rows = conn.execute("""
        SELECT o.* FROM saved_opportunities so
        JOIN opportunities o ON so.opportunity_id = o.id
        WHERE so.user_id = ?
    """, (user_id,)).fetchall()

    today = date.today()
    for opp in saved_rows:
        d = opp["deadline"]
        if d:
            try:
                dt = datetime.strptime(d.strip(), "%Y-%m-%d").date()
                delta = (dt - today).days
                if 0 <= delta <= 35:
                    ref_key = f"deadline_reminder_{opp['id']}_{d}"
                    title = f"⏰ Deadline Reminder: {opp['title'][:55]}"
                    body = f"Application deadline ends on {d} ({delta} day(s) remaining). Verify your documents and apply."
                    link = url_for("opportunity_detail", id=opp["id"])
                    conn.execute("""
                        INSERT OR IGNORE INTO notifications (user_id, kind, title, body, link, ref_key)
                        VALUES (?, 'deadline', ?, ?, ?, ?)
                    """, (user_id, title, body, link, ref_key))
            except Exception:
                pass

    # 2. Real new verified announcement notifications matching user's interests
    user_interests = [i.lower() for i in prefs.get("interests", [])]
    recent_opps = conn.execute("""
        SELECT * FROM opportunities 
        WHERE is_verified = 1
        ORDER BY id DESC LIMIT 12
    """).fetchall()

    for opp in recent_opps:
        cat_lower = (opp["category"] or "").lower()
        if any(i in cat_lower or cat_lower in i for i in user_interests):
            ref_key = f"new_match_{opp['id']}"
            title = f"📢 New in {opp['category']}: {opp['title'][:55]}"
            body = f"A verified notice matching your profile was announced in {opp['location']}."
            link = url_for("opportunity_detail", id=opp["id"])
            conn.execute("""
                INSERT OR IGNORE INTO notifications (user_id, kind, title, body, link, ref_key)
                VALUES (?, 'new_match', ?, ?, ?, ?)
            """, (user_id, title, body, link, ref_key))

    conn.commit()
    unread_count = conn.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
        (user_id,)
    ).fetchone()[0]
    conn.close()
    return unread_count


@app.context_processor
def inject_globals():
    """Injects common template variables across all templates."""
    prefs = get_current_user_preferences()
    saved_ids = get_user_saved_ids(prefs["user_id"])
    
    try:
        unread_notifications = sync_user_notifications(prefs["user_id"])
    except Exception:
        unread_notifications = 0

    return {
        "user_prefs": prefs,
        "saved_count": len(saved_ids),
        "saved_ids": saved_ids,
        "available_locations": Config.AVAILABLE_LOCATIONS,
        "available_interests": Config.AVAILABLE_INTERESTS,
        "core_categories": Config.CORE_CATEGORIES,
        "category_metadata": Config.CATEGORY_METADATA,
        "available_languages": Config.AVAILABLE_LANGUAGES,
        "unread_notifications": unread_notifications,
        "today_str": date.today().strftime("%Y-%m-%d")
    }


# ==============================================================================
# ROUTES
# ==============================================================================

@app.route("/")
def index():
    """Landing homepage with value proposition, search bar, and highlights."""
    prefs = get_current_user_preferences()
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM opportunities LIMIT 8").fetchall()
    conn.close()

    ranked = rank_opportunities(rows, prefs, sort_by="relevance")
    return render_template("index.html", featured=ranked[:6])


@app.route("/preferences", methods=["GET", "POST"])
def preferences():
    """Onboarding and Preferences modification."""
    user_id = session.get("user_id", 1)
    
    if request.method == "POST":
        location = request.form.get("location", Config.DEFAULT_LOCATION).strip()
        language = request.form.get("language", Config.DEFAULT_LANGUAGE).strip()
        user_type = request.form.get("user_type", "student").strip()
        education_level = request.form.get("education_level", "Undergraduate").strip()
        selected_interests = request.form.getlist("interests")

        if not selected_interests:
            selected_interests = ["Agriculture and farming", "Education and scholarships", "Jobs and internships"]

        interests_json = json.dumps(selected_interests)
        session["language"] = language

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO user_preferences (user_id, location, language, interests, education_level, user_type, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                location = excluded.location,
                language = excluded.language,
                interests = excluded.interests,
                education_level = excluded.education_level,
                user_type = excluded.user_type,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, location, language, interests_json, education_level, user_type))
        conn.commit()
        conn.close()

        flash("Your preferences have been saved successfully! Your personalized feed has updated.", "success")
        return redirect(url_for("dashboard"))

    current_prefs = get_current_user_preferences()
    return render_template("preferences.html", current_prefs=current_prefs)


@app.route("/dashboard")
def dashboard():
    """Personalized Dashboard with recommendations, deadlines, and history."""
    prefs = get_current_user_preferences()
    user_id = prefs["user_id"]
    saved_ids = get_user_saved_ids(user_id)

    conn = get_db_connection()
    all_opps = conn.execute("SELECT * FROM opportunities").fetchall()
    
    # Get recently viewed
    recently_viewed_rows = conn.execute("""
        SELECT o.*, rv.viewed_at 
        FROM recently_viewed rv
        JOIN opportunities o ON rv.opportunity_id = o.id
        WHERE rv.user_id = ?
        ORDER BY rv.viewed_at DESC
        LIMIT 4
    """, (user_id,)).fetchall()

    # Get saved preview
    saved_rows = conn.execute("""
        SELECT o.*, so.saved_at
        FROM saved_opportunities so
        JOIN opportunities o ON so.opportunity_id = o.id
        WHERE so.user_id = ?
        ORDER BY so.saved_at DESC
        LIMIT 4
    """, (user_id,)).fetchall()

    conn.close()

    # Rank recommendations based on user preferences
    ranked_opps = rank_opportunities(all_opps, prefs, sort_by="relevance")

    # Filter upcoming active deadlines
    upcoming_deadlines = []
    today = date.today()
    for opp in all_opps:
        d = opp["deadline"]
        if d:
            try:
                deadline_dt = datetime.strptime(d.strip(), "%Y-%m-%d").date()
                delta = (deadline_dt - today).days
                if 0 <= delta <= 45:
                    item_dict = dict(opp)
                    item_dict["days_left"] = delta
                    upcoming_deadlines.append(item_dict)
            except ValueError:
                pass

    upcoming_deadlines.sort(key=lambda x: x["days_left"])

    return render_template(
        "dashboard.html",
        recommendations=ranked_opps[:6],
        upcoming_deadlines=upcoming_deadlines[:5],
        recently_viewed=recently_viewed_rows,
        saved_items=saved_rows,
        total_opportunities_count=len(all_opps)
    )


@app.route("/discover")
def discovery():
    """Smart Local Discovery page with NLP intent understanding, multi-filtering, and category discovery."""
    prefs = get_current_user_preferences()
    
    search_query = request.args.get("q", "").strip()
    
    # Support multiple category query parameters (?category=A&category=B) or single (?category=A)
    selected_categories = [c.strip() for c in request.args.getlist("category") if c.strip()]
    if not selected_categories and request.args.get("category"):
        selected_categories = [request.args.get("category").strip()]
    
    selected_location = request.args.get("location", "").strip()
    selected_trust = request.args.get("trust", "").strip()
    selected_type = request.args.get("type", "").strip()  # 'verified' or 'sample'
    sort_by = request.args.get("sort", "relevance").strip()

    # Query Understanding via Natural Language Parser
    parsed_intent = None
    inferred_category = None
    inferred_location = None

    if search_query:
        parsed_intent = parse_user_query(search_query)
        inferred_category = parsed_intent.get("detected_category")
        inferred_location = parsed_intent.get("detected_location")

    conn = get_db_connection()
    all_rows = conn.execute("SELECT * FROM opportunities").fetchall()
    conn.close()

    # Compute category statistics across the entire database
    category_counts = {}
    for r in all_rows:
        cat = r["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        canon = Config.CATEGORY_CANONICAL_MAP.get(cat.lower(), cat)
        if canon != cat:
            category_counts[canon] = category_counts.get(canon, 0) + 1

    # Active filter category: explicit selection takes precedence over inferred
    effective_categories = selected_categories.copy()
    if not effective_categories and inferred_category:
        effective_categories = [inferred_category]

    # Effective location
    effective_location = selected_location or inferred_location

    filtered_items = []
    
    for r in all_rows:
        d = dict(r)
        cat_lower = (d.get("category") or "").lower()
        canon_cat = Config.CATEGORY_CANONICAL_MAP.get(cat_lower, d.get("category"))
        loc_lower = (d.get("location") or "").lower()

        # 1. Filter by category if specified
        if effective_categories:
            cat_match = False
            for sc in effective_categories:
                sc_lower = sc.lower()
                canon_sc = Config.CATEGORY_CANONICAL_MAP.get(sc_lower, sc)
                if (sc_lower == cat_lower or 
                    canon_sc == canon_cat or
                    sc_lower in cat_lower or 
                    cat_lower in sc_lower):
                    cat_match = True
                    break
            if not cat_match and not (search_query and not selected_categories):
                # When explicit category filter is active, enforce strictly
                if selected_categories:
                    continue

        # 2. Filter by location if specified
        if selected_location:
            sl_lower = selected_location.lower()
            if sl_lower == "other karnataka":
                if "karnataka" not in loc_lower and loc_lower != "other karnataka":
                    continue
            elif sl_lower not in loc_lower and loc_lower not in ["all india", "karnataka statewide", "online"]:
                continue

        # 3. Filter by Data Type (Verified vs Sample) if chosen
        if selected_type == "verified" and d.get("is_sample", 0) == 1:
            continue
        elif selected_type == "sample" and d.get("is_sample", 0) == 0:
            continue

        # 4. Keyword / Intent Content Matching
        match_score_bonus = 0
        if search_query:
            query_lower = search_query.lower()
            text_corpus = " ".join([
                d.get("title") or "",
                d.get("kannada_title") or "",
                d.get("short_description") or "",
                d.get("full_description") or "",
                d.get("kannada_description") or "",
                d.get("eligibility") or "",
                d.get("who_can_benefit") or "",
                d.get("requirements") or "",
                d.get("organization") or "",
                d.get("category") or "",
                d.get("location") or ""
            ]).lower()

            # Exact query substring bonus
            if query_lower in text_corpus:
                match_score_bonus += 35

            # Intent keywords matching
            keywords = parsed_intent.get("clean_keywords", []) if parsed_intent else []
            kw_hits = 0
            for kw in keywords:
                if kw in text_corpus:
                    kw_hits += 1

            if keywords:
                kw_ratio = kw_hits / len(keywords)
                match_score_bonus += int(kw_ratio * 40)
            
            # If category matched intent
            if inferred_category and (inferred_category.lower() in cat_lower or canon_cat == inferred_category):
                match_score_bonus += 25

            # If location matched intent
            if inferred_location and inferred_location.lower() in loc_lower:
                match_score_bonus += 15

            # If user entered specific search terms, require at least some match
            # unless a category filter was matched
            has_content_hit = (kw_hits > 0) or (query_lower in text_corpus)
            cat_hit = bool(inferred_category and (inferred_category.lower() in cat_lower or canon_cat == inferred_category))
            
            # If neither content nor category matched, skip
            if not has_content_hit and not cat_hit and not (effective_categories and cat_match):
                continue

        # Evaluate TrustCheck
        trust_info = evaluate_trust(d)
        d["trust_status"] = trust_info["status"]
        d["trust_badge_class"] = trust_info["badge_class"]
        d["is_official_domain"] = trust_info["is_official_domain"]
        d["trust_warnings_count"] = len(trust_info["warnings"])

        # Filter by Trust Status if selected
        if selected_trust:
            if selected_trust.lower() not in trust_info["status"].lower():
                continue

        d["search_match_bonus"] = match_score_bonus
        filtered_items.append(d)

    # Rank results by recommendation preferences + search bonus
    ranked_items = rank_opportunities(filtered_items, prefs, sort_by=sort_by)
    
    # If search bonus exists, boost top relevance
    if search_query:
        for item in ranked_items:
            item["match_score"] = min(100, item["match_score"] + item.get("search_match_bonus", 0))
        if sort_by == "relevance":
            ranked_items.sort(key=lambda x: x["match_score"], reverse=True)

    # Inferred query human message
    interpretation_note = None
    if parsed_intent and parsed_intent.get("confidence", 0) >= 0.5:
        interpretation_note = parsed_intent.get("interpreted_summary")

    # Clear empty result message
    empty_message = None
    if not ranked_items and search_query:
        loc_msg = f"in {selected_location}" if selected_location else ""
        empty_message = (
            f"No verified opportunities or announcements were found for '{search_query}' {loc_msg}. "
            "We could not find official records matching this specific request. "
            "Try selecting 'All Karnataka', choosing from the category cards below, or searching with broader keywords."
        )

    return render_template(
        "discovery.html",
        opportunities=ranked_items,
        search_query=search_query,
        selected_category=selected_categories[0] if selected_categories else "",
        selected_categories=selected_categories,
        selected_location=selected_location,
        selected_trust=selected_trust,
        selected_type=selected_type,
        sort_by=sort_by,
        total_count=len(ranked_items),
        category_counts=category_counts,
        parsed_intent=parsed_intent,
        interpretation_note=interpretation_note,
        empty_message=empty_message
    )


@app.route("/categories")
def categories():
    """Category-wise Discovery hub displaying all 15 core categories and statistics."""
    return discovery()


@app.route("/set-language/<lang>")
def set_language(lang):
    """Switches the session active language between English and Kannada."""
    raw = (lang or "").strip().lower()
    normalized = "Kannada" if raw.startswith("k") or "kn" in raw else "English"
    session["language"] = normalized

    # Update in DB user_preferences if user row exists
    user_id = session.get("user_id", 1)
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE user_preferences SET language = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (normalized, user_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("[set_language] update notice:", e)

    referrer = request.referrer
    if referrer and "/set-language" not in referrer:
        return redirect(referrer)
    return redirect(url_for("discovery"))


@app.route("/notifications")
def notifications_view():
    """Alerts and Notification center displaying deadline reminders and new opportunity matches."""
    user_id = session.get("user_id", 1)
    sync_user_notifications(user_id)
    
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    
    # Mark as read
    conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    return render_template("dashboard.html", notifications_list=rows, show_notifications=True)


@app.route("/api/notifications")
def api_notifications():
    """Returns JSON list of notifications and unread count."""
    user_id = session.get("user_id", 1)
    unread = sync_user_notifications(user_id)
    
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()
    conn.close()

    items = [dict(r) for r in rows]
    return jsonify({"success": True, "unread_count": unread, "notifications": items})


@app.route("/api/notifications/read/<int:id>", methods=["POST"])
def api_mark_notification_read(id):
    """Marks a single notification as read."""
    user_id = session.get("user_id", 1)
    conn = get_db_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    unread = conn.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,)).fetchone()[0]
    conn.close()
    return jsonify({"success": True, "unread_count": unread})


@app.route("/opportunity/<int:id>")
def opportunity_detail(id):
    """Opportunity Detail view with AI Summary, TrustCheck, and Audio player."""
    user_id = session.get("user_id", 1)
    prefs = get_current_user_preferences()

    conn = get_db_connection()
    opp = conn.execute("SELECT * FROM opportunities WHERE id = ?", (id,)).fetchone()
    
    if not opp:
        conn.close()
        flash("Opportunity not found.", "danger")
        return redirect(url_for("discovery"))

    opp_dict = dict(opp)

    # Record recently viewed
    conn.execute("""
        INSERT INTO recently_viewed (user_id, opportunity_id, viewed_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (user_id, id))
    conn.commit()
    conn.close()

    # Calculate match & TrustCheck
    match_info = calculate_match_score(opp_dict, prefs)
    trust_info = evaluate_trust(opp_dict)
    
    # Generate structured AI summary in user's preferred language
    lang = request.args.get("lang", prefs["language"])
    summary = generate_summary(opp_dict, language=lang)

    return render_template(
        "opportunity_detail.html",
        opp=opp_dict,
        match_info=match_info,
        trust_info=trust_info,
        summary=summary,
        current_lang=lang
    )


@app.route("/saved")
def saved_opportunities():
    """List of all bookmarked opportunities for current user."""
    user_id = session.get("user_id", 1)
    prefs = get_current_user_preferences()

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT o.*, so.saved_at
        FROM saved_opportunities so
        JOIN opportunities o ON so.opportunity_id = o.id
        WHERE so.user_id = ?
        ORDER BY so.saved_at DESC
    """, (user_id,)).fetchall()
    conn.close()

    ranked = rank_opportunities(rows, prefs, sort_by="relevance")
    return render_template("saved.html", saved_list=ranked)


# ==============================================================================
# API ENDPOINTS (AJAX / AUDIO)
# ==============================================================================

@app.route("/api/save/<int:id>", methods=["POST"])
def api_toggle_save(id):
    """AJAX endpoint to bookmark/unbookmark an opportunity."""
    user_id = session.get("user_id", 1)
    conn = get_db_connection()
    
    existing = conn.execute(
        "SELECT id FROM saved_opportunities WHERE user_id = ? AND opportunity_id = ?",
        (user_id, id)
    ).fetchone()

    if existing:
        conn.execute(
            "DELETE FROM saved_opportunities WHERE user_id = ? AND opportunity_id = ?",
            (user_id, id)
        )
        saved = False
        message = "Removed from your saved list."
    else:
        conn.execute(
            "INSERT INTO saved_opportunities (user_id, opportunity_id) VALUES (?, ?)",
            (user_id, id)
        )
        saved = True
        message = "Saved to your bookmarks!"

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM saved_opportunities WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()

    return jsonify({"success": True, "saved": saved, "count": count, "message": message})


@app.route("/api/listen/<int:id>")
def api_listen_opportunity(id):
    """Provides speech text and metadata for browser speech synthesis in English or Kannada."""
    raw_lang = request.args.get("lang", "English").strip()
    conn = get_db_connection()
    opp = conn.execute("SELECT * FROM opportunities WHERE id = ?", (id,)).fetchone()
    conn.close()

    if not opp:
        return jsonify({"success": False, "error": "Opportunity not found"}), 404

    opp_dict = dict(opp)
    summary = generate_summary(opp_dict, language=raw_lang)

    # Determine canonical title for audio dock
    resolved_lang = summary.get("language", "English")
    if resolved_lang == "Kannada" and opp_dict.get("kannada_title"):
        audio_title = opp_dict["kannada_title"]
    else:
        audio_title = opp_dict.get("title")

    return jsonify({
        "success": True,
        "id": id,
        "title": audio_title,
        "raw_title": opp_dict.get("title"),
        "kannada_title": opp_dict.get("kannada_title"),
        "language": resolved_lang,
        "lang_code": summary.get("lang_code", "kn-IN" if resolved_lang == "Kannada" else "en-IN"),
        "speech_text": summary.get("speech_text"),
        "what_is_it": summary.get("what_is_it"),
        "provider": summary.get("provider")
    })


# ==============================================================================
# ADMIN MANAGEMENT
# ==============================================================================

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    """Admin interface for data management."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        kannada_title = request.form.get("kannada_title", "").strip()
        category = request.form.get("category", "").strip()
        organization = request.form.get("organization", "").strip()
        location = request.form.get("location", "").strip()
        short_description = request.form.get("short_description", "").strip()
        full_description = request.form.get("full_description", "").strip()
        kannada_description = request.form.get("kannada_description", "").strip()
        eligibility = request.form.get("eligibility", "").strip()
        requirements = request.form.get("requirements", "").strip()
        deadline = request.form.get("deadline", "").strip() or None
        publication_date = request.form.get("publication_date", "").strip() or date.today().strftime("%Y-%m-%d")
        source_name = request.form.get("source_name", "").strip()
        source_url = request.form.get("source_url", "").strip()
        how_to_apply = request.form.get("how_to_apply", "").strip()
        who_can_benefit = request.form.get("who_can_benefit", "").strip()
        is_verified = 1 if request.form.get("is_verified") == "1" else 0

        # Basic form validation
        if not title or not category or not organization or not short_description:
            flash("Validation Error: Title, Category, Organization, and Short Description are required.", "danger")
            return redirect(url_for("admin_dashboard"))

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO opportunities (
                title, kannada_title, category, organization, location,
                short_description, full_description, kannada_description,
                eligibility, requirements, deadline, publication_date,
                source_name, source_url, how_to_apply, who_can_benefit,
                last_updated_date, is_sample, is_verified, last_checked_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            title, kannada_title, category, organization, location,
            short_description, full_description or short_description,
            kannada_description, eligibility, requirements, deadline,
            publication_date, source_name, source_url, how_to_apply,
            who_can_benefit, publication_date, is_verified, date.today().strftime("%Y-%m-%d")
        ))
        conn.commit()
        conn.close()

        flash(f"Opportunity '{title}' added successfully! Marked as SAMPLE DATA for demo safety.", "success")
        return redirect(url_for("admin_dashboard"))

    conn = get_db_connection()
    opportunities = conn.execute("SELECT * FROM opportunities ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("admin.html", opportunities=opportunities)


@app.route("/admin/edit/<int:id>", methods=["GET", "POST"])
def admin_edit(id):
    """Edit an existing opportunity record."""
    conn = get_db_connection()
    opp = conn.execute("SELECT * FROM opportunities WHERE id = ?", (id,)).fetchone()

    if not opp:
        conn.close()
        flash("Record not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        kannada_title = request.form.get("kannada_title", "").strip()
        category = request.form.get("category", "").strip()
        organization = request.form.get("organization", "").strip()
        location = request.form.get("location", "").strip()
        short_description = request.form.get("short_description", "").strip()
        full_description = request.form.get("full_description", "").strip()
        kannada_description = request.form.get("kannada_description", "").strip()
        eligibility = request.form.get("eligibility", "").strip()
        requirements = request.form.get("requirements", "").strip()
        deadline = request.form.get("deadline", "").strip() or None
        publication_date = request.form.get("publication_date", "").strip()
        source_name = request.form.get("source_name", "").strip()
        source_url = request.form.get("source_url", "").strip()
        how_to_apply = request.form.get("how_to_apply", "").strip()
        who_can_benefit = request.form.get("who_can_benefit", "").strip()
        is_verified = 1 if request.form.get("is_verified") == "1" else 0

        conn.execute("""
            UPDATE opportunities SET
                title = ?, kannada_title = ?, category = ?, organization = ?, location = ?,
                short_description = ?, full_description = ?, kannada_description = ?,
                eligibility = ?, requirements = ?, deadline = ?, publication_date = ?,
                source_name = ?, source_url = ?, how_to_apply = ?, who_can_benefit = ?,
                is_verified = ?, last_checked_date = ?
            WHERE id = ?
        """, (
            title, kannada_title, category, organization, location,
            short_description, full_description, kannada_description,
            eligibility, requirements, deadline, publication_date,
            source_name, source_url, how_to_apply, who_can_benefit,
            is_verified, date.today().strftime("%Y-%m-%d"), id
        ))
        conn.commit()
        conn.close()

        flash("Opportunity updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    return render_template("admin_edit.html", opp=dict(opp))


@app.route("/admin/delete/<int:id>", methods=["POST"])
def admin_delete(id):
    """Safely delete an opportunity record."""
    conn = get_db_connection()
    conn.execute("DELETE FROM opportunities WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Opportunity record removed.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reset-demo", methods=["POST"])
def admin_reset_demo():
    """Resets the database back to clean initial demo state."""
    count = seed_database()
    flash(f"Database successfully re-seeded with {count} sample records for hackathon presentation.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/about")
def about():
    """About page with hackathon background, architecture, and team info."""
    return render_template("about.html")


if __name__ == "__main__":
    # Local development server
    app.run(host="127.0.0.1", port=5000, debug=True)
