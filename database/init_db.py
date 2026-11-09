import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_db_connection, init_db
from database.seed_data import SAMPLE_OPPORTUNITIES
from database.seed_news import COMPLETE_NEWS_DATA

def seed_database():
    """Initializes tables and seeds demo opportunities and verified news articles."""
    init_db(force_recreate=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Seed Opportunities
    for item in SAMPLE_OPPORTUNITIES:
        cursor.execute("""
            INSERT INTO opportunities (
                title, kannada_title, category, organization, location,
                short_description, full_description, kannada_description,
                eligibility, requirements, deadline, publication_date,
                source_name, source_url, how_to_apply, who_can_benefit,
                last_updated_date, is_sample, is_verified, last_checked_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["title"],
            item.get("kannada_title", ""),
            item["category"],
            item["organization"],
            item["location"],
            item["short_description"],
            item["full_description"],
            item.get("kannada_description", ""),
            item.get("eligibility", ""),
            item.get("requirements", ""),
            item.get("deadline", ""),
            item.get("publication_date", ""),
            item.get("source_name", ""),
            item.get("source_url", ""),
            item.get("how_to_apply", ""),
            item.get("who_can_benefit", ""),
            item.get("last_updated_date", item.get("publication_date", "")),
            item.get("is_sample", 1),
            item.get("is_verified", 0),
            item.get("last_checked_date", "")
        ))

    # 2. Seed Complete News Articles
    for news in COMPLETE_NEWS_DATA:
        cursor.execute("""
            INSERT INTO news_articles (
                category, original_headline, publisher_name, source_url,
                publication_date, publication_time, last_updated_date,
                location, is_official_government, verification_status,
                original_language, multilingual_content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            news["category"],
            news["original_headline"],
            news["publisher_name"],
            news["source_url"],
            news["publication_date"],
            news.get("publication_time", "10:00 AM IST"),
            news.get("last_updated_date", news["publication_date"]),
            news["location"],
            news.get("is_official_government", 1),
            news.get("verification_status", "Verified Official Notification"),
            news.get("original_language", "English"),
            json.dumps(news["multilingual_content"], ensure_ascii=False)
        ))

    conn.commit()
    opp_count = cursor.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    news_count = cursor.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
    conn.close()

    print(f"Successfully seeded database with {opp_count} opportunities and {news_count} complete news articles.")
    return opp_count + news_count

if __name__ == "__main__":
    seed_database()
