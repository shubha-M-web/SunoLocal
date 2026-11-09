"""Query, trust labelling, and in-app alerts for news items."""

import json
from datetime import datetime, date

from config import Config
from database.db import get_db_connection
from modules.trustcheck import evaluate_news_trust
from modules.translator import get_article_content


KARNATAKA_LOCATIONS = {
    "mysuru", "bengaluru", "mandya", "other karnataka",
    "karnataka statewide", "karnataka",
}


def list_news(filters, language="English"):
    sql = "SELECT * FROM news_articles WHERE 1=1"
    params = []

    category = (filters.get("category") or "").strip()
    if category:
        sql += " AND category = ?"
        params.append(category)

    subcategory = (filters.get("subcategory") or "").strip()
    if subcategory:
        sql += " AND subcategory = ?"
        params.append(subcategory)

    location = (filters.get("location") or "").strip()
    if location:
        sql += " AND location = ?"
        params.append(location)

    state = (filters.get("state") or "").strip()
    if state == "Karnataka":
        sql += " AND (location IN ('Mysuru', 'Bengaluru', 'Mandya', 'Other Karnataka', 'Karnataka Statewide') OR location LIKE '%Karnataka%')"
    elif state and state != "All":
        sql += " AND (location = ? OR location = 'All India')"
        params.append(state)

    query = (filters.get("q") or "").strip()
    if query:
        sql += " AND (original_headline LIKE ? OR publisher_name LIKE ? OR location LIKE ? OR multilingual_content LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term, term])

    source = (filters.get("source") or "").strip()
    if source:
        sql += " AND publisher_name LIKE ?"
        params.append(f"%{source}%")

    date_from = (filters.get("date_from") or "").strip()
    if date_from:
        sql += " AND publication_date >= ?"
        params.append(date_from)
    date_to = (filters.get("date_to") or "").strip()
    if date_to:
        sql += " AND publication_date <= ?"
        params.append(date_to)

    sort = (filters.get("sort") or "latest").strip()
    if sort == "oldest":
        sql += " ORDER BY publication_date ASC, id ASC"
    else:
        sql += " ORDER BY publication_date DESC, id DESC"

    conn = get_db_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    items = []
    for row in rows:
        item = dict(row)
        content = get_article_content(item, language)
        trust = evaluate_news_trust(item)
        item["display_headline"] = content.get("headline") or item["original_headline"]
        item["display_lead"] = (content.get("full_explanation") or "")[:280]
        item["content_language"] = content.get("language")
        item["translation_notice"] = content.get("translation_notice")
        item["trust"] = trust
        items.append(item)
    return items


def get_news_or_none(news_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM news_articles WHERE id = ?", (news_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def related_news(article, language, limit=3):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT * FROM news_articles
        WHERE category = ? AND id != ?
        ORDER BY publication_date DESC
        LIMIT ?
        """,
        (article["category"], article["id"], limit),
    ).fetchall()
    conn.close()
    items = []
    for row in rows:
        data = dict(row)
        content = get_article_content(data, language)
        data["display_headline"] = content.get("headline") or data["original_headline"]
        items.append(data)
    return items


def record_news_view(user_id, news_id):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO recently_viewed_news (user_id, news_id) VALUES (?, ?)",
        (user_id, news_id),
    )
    conn.commit()
    conn.close()


def saved_news_ids(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT news_id FROM saved_news WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return {row["news_id"] for row in rows}


def toggle_saved_news(user_id, news_id):
    conn = get_db_connection()
    existing = conn.execute(
        "SELECT id FROM saved_news WHERE user_id = ? AND news_id = ?",
        (user_id, news_id),
    ).fetchone()
    if existing:
        conn.execute(
            "DELETE FROM saved_news WHERE user_id = ? AND news_id = ?",
            (user_id, news_id),
        )
        saved = False
        message = "Removed from saved news."
    else:
        conn.execute(
            "INSERT INTO saved_news (user_id, news_id) VALUES (?, ?)",
            (user_id, news_id),
        )
        saved = True
        message = "News saved."
    conn.commit()
    count = conn.execute(
        "SELECT COUNT(*) FROM saved_news WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]
    conn.close()
    return {"success": True, "saved": saved, "count": count, "message": message}


def news_for_user_type(user_type, language, limit=4):
    categories = Config.USER_TYPE_NEWS.get(user_type or "student", Config.USER_TYPE_NEWS["student"])
    if not categories:
        return []
    placeholders = ",".join("?" for _ in categories)
    conn = get_db_connection()
    rows = conn.execute(
        f"""
        SELECT * FROM news_articles
        WHERE category IN ({placeholders})
        ORDER BY publication_date DESC, id DESC
        LIMIT ?
        """,
        (*categories, limit),
    ).fetchall()
    conn.close()
    items = []
    for row in rows:
        data = dict(row)
        content = get_article_content(data, language)
        data["display_headline"] = content.get("headline") or data["original_headline"]
        data["display_lead"] = (content.get("full_explanation") or "")[:180]
        data["trust"] = evaluate_news_trust(data)
        items.append(data)
    return items


def sync_notifications(user_id, prefs):
    """Creates in-app alerts from stored deadlines and matching news. Does not invent alerts."""
    alert_prefs = _alert_prefs(prefs)
    conn = get_db_connection()
    today = date.today()

    if alert_prefs.get("deadlines", True) or alert_prefs.get("schemes", True):
        rows = conn.execute("SELECT id, title, deadline, category FROM opportunities").fetchall()
        for row in rows:
            if not row["deadline"]:
                continue
            try:
                deadline = datetime.strptime(row["deadline"].strip(), "%Y-%m-%d").date()
            except ValueError:
                continue
            days = (deadline - today).days
            if not (0 <= days <= 21):
                continue
            _insert_notification(
                conn,
                user_id,
                "deadline",
                f"Deadline in {days} day(s): {row['title']}",
                f"The stored deadline is {row['deadline']}. Confirm it on the official source before you apply.",
                f"/opportunity/{row['id']}",
                f"deadline-{row['id']}-{row['deadline']}",
            )

    if alert_prefs.get("news", True):
        categories = Config.USER_TYPE_NEWS.get(prefs.get("user_type") or "student", [])
        if categories:
            placeholders = ",".join("?" for _ in categories)
            news_rows = conn.execute(
                f"""
                SELECT id, original_headline, category, is_sample
                FROM news_articles
                WHERE category IN ({placeholders})
                ORDER BY publication_date DESC
                LIMIT 6
                """,
                tuple(categories),
            ).fetchall()
            for row in news_rows:
                label = "Demonstration update" if row["is_sample"] else "New update"
                _insert_notification(
                    conn,
                    user_id,
                    "news",
                    f"{label}: {row['original_headline'][:110]}",
                    f"A {row['category']} item is available in your hub. Open it for the full explanation and source.",
                    f"/news/article/{row['id']}",
                    f"news-{row['id']}",
                )

    conn.commit()
    conn.close()


def list_notifications(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 40
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def unread_count(user_id):
    conn = get_db_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
        (user_id,),
    ).fetchone()[0]
    conn.close()
    return count


def mark_notifications_read(user_id):
    conn = get_db_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def _insert_notification(conn, user_id, kind, title, body, link, ref_key):
    conn.execute(
        """
        INSERT INTO notifications (user_id, kind, title, body, link, ref_key)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, ref_key) DO NOTHING
        """,
        (user_id, kind, title, body, link, ref_key),
    )


def _alert_prefs(prefs):
    raw = prefs.get("alert_prefs")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return {"news": True, "deadlines": True, "schemes": True}
