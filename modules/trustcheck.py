"""
TrustCheck Module for SunoLocal.
Assesses information transparency, source integrity, and freshness.
Designed to protect students against unverified circulars, fake deadlines, and scam forwards.
"""

from datetime import datetime, date
from urllib.parse import urlparse

OFFICIAL_DOMAINS = [
    ".gov.in",
    ".karnataka.gov.in",
    ".nic.in",
    ".ac.in",
    ".edu.in",
    ".res.in",
    ".org.in",
    "onwingspan.com",
    "ksca.cricket",
    "ksndmc.org",
    "kscst.org.in",
    "rangayana.org",
    "kdem.karnataka.gov.in",
    "sevasindhugs.karnataka.gov.in",
    "ssp.postmatric.karnataka.gov.in",
    "raitamitra.karnataka.gov.in",
    "cftri.res.in",
    "kviconline.gov.in",
    "scholarships.gov.in",
    "telemanas.mohfw.gov.in",
    "nats.education.gov.in",
    "startup.karnataka.gov.in",
    "mysurucitycorporation.co.in"
]

def evaluate_trust(opportunity):
    """
    Evaluates an opportunity's transparency, source, and validity.
    
    Returns:
        dict containing:
            - status: str (e.g. 'Source available', 'Requires manual verification', etc.)
            - badge_class: str ('status-success', 'status-warning', 'status-danger', etc.)
            - source_url: str or None
            - source_name: str
            - publication_date: str or None
            - last_checked_date: str or None
            - is_official_domain: bool
            - is_expired: bool
            - days_remaining: int or None
            - warnings: list of str
            - positive_signals: list of str
            - disclaimer: str
    """
    opp = dict(opportunity) if not isinstance(opportunity, dict) else opportunity
    warnings = []
    positive_signals = []
    
    source_url = (opp.get("source_url") or "").strip()
    source_name = (opp.get("source_name") or "").strip()
    publication_date = opp.get("publication_date")
    last_checked_date = opp.get("last_checked_date")
    deadline = opp.get("deadline")
    eligibility = (opp.get("eligibility") or "").strip()
    how_to_apply = (opp.get("how_to_apply") or "").strip()
    is_verified = bool(opp.get("is_verified", 0))

    is_official_domain = False
    domain_name = ""
    is_expired = False
    days_remaining = None

    # 1. Source Link Check
    if not source_url:
        warnings.append("Source Missing: No original link or official document URL was provided.")
    else:
        try:
            parsed = urlparse(source_url)
            domain_name = parsed.netloc.lower()
            if any(domain_name.endswith(ext) or ext in domain_name for ext in OFFICIAL_DOMAINS):
                is_official_domain = True
                positive_signals.append(f"Official Institutional Domain detected ({domain_name})")
            else:
                positive_signals.append(f"External Source Link provided ({domain_name})")
        except Exception:
            warnings.append("Malformed URL: Source link could not be parsed.")

    # 2. Source Name Check
    if not source_name or "unknown" in source_name.lower() or "unverified" in source_name.lower():
        warnings.append("Unverified Origin: Source publisher is unknown or marked as social forward.")
    else:
        positive_signals.append(f"Publisher Identified: {source_name}")

    # 3. Date & Freshness Check
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline.strip(), "%Y-%m-%d").date()
            today = date.today()
            delta = (deadline_date - today).days
            days_remaining = delta

            if delta < 0:
                is_expired = True
                warnings.append(f"Potentially Outdated: Application deadline ended on {deadline}.")
            elif delta <= 5:
                warnings.append(f"Urgent Deadline: Closes in {delta} day(s). Verify requirements immediately.")
            else:
                positive_signals.append(f"Active Deadline: {delta} days remaining (Closes {deadline}).")
        except ValueError:
            warnings.append("Date Format Notice: Deadline could not be parsed.")
    else:
        warnings.append("Date Unavailable: No specific closing date was specified in this posting.")

    # 4. Publication Date Check
    if not publication_date:
        warnings.append("Publication Date Missing: Release date could not be confirmed.")
    else:
        positive_signals.append(f"Published on: {publication_date}")

    # 5. Completeness Checks
    if not eligibility or len(eligibility) < 10:
        warnings.append("Incomplete Criteria: Explicit eligibility criteria are missing.")
    if not how_to_apply or len(how_to_apply) < 15:
        warnings.append("Application Steps Incomplete: No clear instructions on how to apply.")

    # 6. Overall Status Classification
    if not source_url:
        status = "Source missing"
        badge_class = "status-danger"
    elif is_expired:
        status = "Potentially outdated"
        badge_class = "status-danger"
    elif not deadline:
        status = "Date unavailable"
        badge_class = "status-warning"
    elif not is_verified and not is_official_domain:
        status = "Requires manual verification"
        badge_class = "status-warning"
    else:
        status = "Source available"
        badge_class = "status-success"

    disclaimer = (
        "IMPORTANT: SunoLocal TrustCheck audits information quality and source links. "
        "A working source link does not prove that all information is authentic or correct. "
        "Always cross-check with the official institutional portal before submitting sensitive personal data or fees."
    )

    return {
        "status": status,
        "badge_class": badge_class,
        "source_url": source_url,
        "source_name": source_name or "Not Specified",
        "domain_name": domain_name,
        "publication_date": publication_date,
        "last_checked_date": last_checked_date or "Recently Checked",
        "is_official_domain": is_official_domain,
        "is_expired": is_expired,
        "days_remaining": days_remaining,
        "warnings": warnings,
        "positive_signals": positive_signals,
        "disclaimer": disclaimer,
        "is_officially_verified": is_verified
    }


def evaluate_news_trust(article):
    """
    Labels where a news record came from.
    A known website is not treated as proof that every claim is true.
    """
    item = dict(article)
    source_url = (item.get("source_url") or "").strip()
    source_name = (item.get("publisher_name") or "").strip() or "Not available in the source"
    warnings = []
    domain_name = ""
    is_official_domain = False

    if not source_url:
        warnings.append("Original URL is not stored.")
        label = "Source Not Verified"
        badge_class = "status-danger"
    else:
        try:
            domain_name = urlparse(source_url).netloc.lower()
        except Exception:
            domain_name = ""
            warnings.append("The source link could not be read.")
        is_official_domain = bool(domain_name) and any(
            domain_name.endswith(ext) or ext in domain_name for ext in OFFICIAL_DOMAINS
        )
        if item.get("is_sample"):
            warnings.append("This is a demonstration record, not a live notice fetched today.")
        if is_official_domain or item.get("source_class") == "official" or item.get("is_official_government"):
            label = "Official Government Source"
            badge_class = "status-success"
        elif item.get("source_class") == "sports_body":
            label = "Reputable News Publisher"
            badge_class = "status-success"
        elif source_name and "unknown" not in source_name.lower():
            label = "Reputable News Publisher"
            badge_class = "status-warning"
        else:
            label = "Source Not Verified"
            badge_class = "status-danger"

    references = item.get("official_references") or ""
    if isinstance(references, str) and references.count("http") + references.count(";") >= 1 and " and " in references.lower():
        label = "Multiple Sources Available"

    missing_bits = []
    if not item.get("publication_date"):
        missing_bits.append("publication date")
    if not item.get("last_updated_date"):
        missing_bits.append("last updated date")
    if missing_bits:
        warnings.append("Information Incomplete: " + ", ".join(missing_bits) + " not stored.")
        if label == "Source Not Verified":
            label = "Information Incomplete"
            badge_class = "status-warning"

    return {
        "label": label,
        "badge_class": badge_class,
        "source_name": source_name,
        "source_url": source_url,
        "domain_name": domain_name,
        "publication_date": item.get("publication_date"),
        "last_updated_date": item.get("last_updated_date"),
        "fetched_at": item.get("fetched_at"),
        "is_official_domain": is_official_domain,
        "is_sample": bool(item.get("is_sample", 1)),
        "warnings": warnings,
        "disclaimer": (
            "TrustCheck shows who published the record and whether the link looks official. "
            "That is not a fact-check. Confirm important rules and scheme benefits on the government notification."
        ),
    }
