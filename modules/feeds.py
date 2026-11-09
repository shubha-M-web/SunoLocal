"""
Optional public RSS refresh.

Stores the feed title, link, date, and a short lead. It does not copy a full
copyrighted article. Items are marked as live feed records, separate from
demonstration explanations.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

from config import Config
from database.db import get_db_connection

NS = {"dc": "http://purl.org/dc/elements/1.1/"}


def refresh_feeds():
    """Fetches configured RSS feeds. Returns a status dict and never fabricates items."""
    inserted = 0
    errors = []
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for feed in Config.RSS_FEEDS:
        try:
            response = requests.get(
                feed["url"],
                timeout=12,
                headers={"User-Agent": "SunoLocal/1.0 (local information demo; +https://pib.gov.in/)"},
            )
            response.raise_for_status()
            inserted += _store_feed(feed, response.content, fetched_at)
        except Exception as exc:
            errors.append(f"{feed['name']}: {exc}")

    return {
        "inserted": inserted,
        "errors": errors,
        "fetched_at": fetched_at,
        "feeds": len(Config.RSS_FEEDS),
    }


def _store_feed(feed, raw_xml, fetched_at):
    root = ET.fromstring(raw_xml)
    items = root.findall(".//item")
    if not items:
        raise ValueError("Feed returned no items")

    conn = get_db_connection()
    added = 0
    try:
        for item in items[:12]:
            title = _text(item, "title")
            link = _text(item, "link")
            if not title or not link or not link.startswith("http"):
                continue
            existing = conn.execute(
                "SELECT id FROM news_articles WHERE source_url = ?",
                (link,),
            ).fetchone()
            if existing:
                continue

            published = _published_date(item)
            lead = _text(item, "description")
            lead = _strip_tags(lead)[:500]
            explanation = (
                "This item was collected from an official public RSS feed. "
                "SunoLocal stores the title and a short lead only, then links to the original notice. "
                "A full translation is not stored for this live item. "
                + (f"Feed lead: {lead}" if lead else "A description was not included in the feed.")
            )
            content = {
                "English": {
                    "headline": title,
                    "full_explanation": explanation,
                    "important_entities": feed["name"],
                    "key_figures_and_dates": f"Publication date from the feed: {published}. Fetch time: {fetched_at}.",
                    "background_and_reasons": "Not available in the source beyond the feed title and lead.",
                    "citizen_impact": "Not available in the source. Open the original notice.",
                    "actionable_steps": "Open the original source link and follow only the instructions published there.",
                    "official_references": feed["name"],
                    "speech_text": f"Live update from {feed['name']}. {title}. Open the original link on SunoLocal for the full notice. This is not a translated version.",
                    "category_details": {},
                }
            }
            conn.execute(
                """
                INSERT INTO news_articles (
                    category, subcategory, original_headline, publisher_name, source_url,
                    publication_date, publication_time, last_updated_date, location,
                    is_official_government, verification_status, original_language,
                    multilingual_content, is_sample, fetched_at, source_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    feed["category"],
                    feed.get("subcategory"),
                    title,
                    feed["name"],
                    link,
                    published,
                    "",
                    published,
                    feed.get("location", "All India"),
                    feed.get("is_official_government", 0),
                    "Live feed item. Source authenticity is not the same as a fact check.",
                    "English",
                    __import__("json").dumps(content, ensure_ascii=False),
                    fetched_at,
                    feed.get("source_class", "official"),
                ),
            )
            added += 1
        conn.commit()
    finally:
        conn.close()
    return added


def _text(item, tag):
    node = item.find(tag)
    if node is None or not node.text:
        return ""
    return " ".join(node.text.split())


def _strip_tags(value):
    out = []
    inside = False
    for char in value or "":
        if char == "<":
            inside = True
            continue
        if char == ">":
            inside = False
            continue
        if not inside:
            out.append(char)
    return " ".join("".join(out).split())


def _published_date(item):
    raw = _text(item, "pubDate") or _text(item, "{http://purl.org/dc/elements/1.1/}date")
    if not raw:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except Exception:
        if len(raw) >= 10 and raw[4] == "-":
            return raw[:10]
        return datetime.now().strftime("%Y-%m-%d")
