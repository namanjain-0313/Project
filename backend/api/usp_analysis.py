# backend/api/usp_analysis.py
# Contains both USP algorithms:
# USP 1 — Narrative Warfare Detection
# USP 2 — Strategic Blind Spot Detector
#
# Called by /api/intelligence-alerts endpoint in main.py
# No new databases, no new APIs — works entirely on existing Neo4j data

import logging
from collections import defaultdict
from neo4j import GraphDatabase
import os

logger = logging.getLogger(__name__)


# ─── SOURCE CLASSIFICATION ───────────────────────────────────────
# Maps domain → country and media type
# Used by USP 1 to detect cross-country narrative synchronisation
# "state" = government controlled, "independent" = private

SOURCE_CLASSIFICATION = {
    # Chinese state media
    "xinhuanet.com":       {"country": "CHN", "type": "state"},
    "globaltimes.cn":      {"country": "CHN", "type": "state"},
    "chinadaily.com.cn":   {"country": "CHN", "type": "state"},
    "cgtn.com":            {"country": "CHN", "type": "state"},
    "peopledaily.com.cn":  {"country": "CHN", "type": "state"},

    # Pakistani media
    "radio.gov.pk":        {"country": "PAK", "type": "state"},
    "app.com.pk":          {"country": "PAK", "type": "state"},
    "dawn.com":            {"country": "PAK", "type": "independent"},
    "geo.tv":              {"country": "PAK", "type": "independent"},
    "thenews.com.pk":      {"country": "PAK", "type": "independent"},
    "arynews.tv":          {"country": "PAK", "type": "independent"},

    # Indian media
    "timesofindia.com":    {"country": "IND", "type": "independent"},
    "thehindu.com":        {"country": "IND", "type": "independent"},
    "ndtv.com":            {"country": "IND", "type": "independent"},
    "hindustantimes.com":  {"country": "IND", "type": "independent"},
    "indianexpress.com":   {"country": "IND", "type": "independent"},
    "ani.com":             {"country": "IND", "type": "independent"},
    "pib.gov.in":          {"country": "IND", "type": "state"},
    "mea.gov.in":          {"country": "IND", "type": "state"},

    # Russian media
    "rt.com":              {"country": "RUS", "type": "state"},
    "tass.com":            {"country": "RUS", "type": "state"},
    "sputniknews.com":     {"country": "RUS", "type": "state"},

    # International
    "reuters.com":         {"country": "INT", "type": "independent"},
    "apnews.com":          {"country": "INT", "type": "independent"},
    "aljazeera.com":       {"country": "QAT", "type": "state"},
    "bbc.com":             {"country": "GBR", "type": "independent"},
    "bbc.co.uk":           {"country": "GBR", "type": "independent"},
    "france24.com":        {"country": "FRA", "type": "state"},
}


def classify_source(url: str) -> dict:
    """Classify a source URL by country and media type"""
    if not url:
        return {"country": "UNK", "type": "unknown"}
    for domain, info in SOURCE_CLASSIFICATION.items():
        if domain in url:
            return info
    return {"country": "UNK", "type": "unknown"}


def get_driver():
    """Get Neo4j driver — reuses connection from environment"""
    return GraphDatabase.driver(
        os.environ["NEO4J_URL"],
        auth=(os.environ.get("NEO4J_USERNAME", "neo4j"),
              os.environ["NEO4J_PASSWORD"])
    )


# ═══════════════════════════════════════════════════════════════════
# USP 1: NARRATIVE WARFARE DETECTION
# ═══════════════════════════════════════════════════════════════════
#
# WHAT IT DETECTS:
# When media from multiple countries starts reporting the SAME
# topic with the SAME tone simultaneously, that synchronisation
# is statistically abnormal. Natural news coverage diverges.
# Coordinated campaigns converge.
#
# HOW THE SCORE WORKS:
# 1. Group events by topic (actor pair e.g. India-China)
# 2. For each topic, separate events by source country
# 3. Average the AvgTone for each country's coverage
# 4. Measure variance — low variance = everyone saying same thing
# 5. Convert low variance to high sync score (0 to 1)
# 6. Boost if state media is involved
# 7. Alert if score crosses threshold
# ═══════════════════════════════════════════════════════════════════

def detect_narrative_warfare(hours_back: int = 48) -> list[dict]:
    """
    Scan recent events for coordinated narrative campaigns.
    Returns alerts ordered by severity.
    """

    # Pull recent events from Neo4j
    with get_driver().session() as session:
        result = session.run("""
            MATCH (e:Event)
            WHERE e.date >= toString(date() - duration({days: 3}))
            AND e.source_url IS NOT NULL
            AND e.avg_tone IS NOT NULL
            RETURN e.actor1          AS actor1,
                   e.actor2          AS actor2,
                   e.avg_tone        AS tone,
                   e.goldstein_score AS goldstein,
                   e.source_url      AS source_url,
                   e.num_mentions    AS mentions,
                   e.event_label     AS event_label,
                   e.date            AS date
        """)
        events = [dict(r) for r in result]

    if not events:
        logger.info("No events found for narrative warfare analysis")
        return []

    # Tag each event with source country and type
    for event in events:
        source_info = classify_source(event.get("source_url", ""))
        event["source_country"] = source_info["country"]
        event["source_type"]    = source_info["type"]

    # Group events by topic (sorted actor pair so order doesn't matter)
    topics = defaultdict(list)
    for event in events:
        a1 = str(event.get("actor1") or "").strip()
        a2 = str(event.get("actor2") or "").strip()
        if a1 and a2 and a1 != a2:
            key = tuple(sorted([a1, a2]))
            topics[key].append(event)

    alerts = []

    for topic, topic_events in topics.items():

        # Need events from at least 2 foreign source countries
        # (excluding India and unknown sources)
        source_countries = set(
            e["source_country"] for e in topic_events
            if e["source_country"] not in ["UNK", "IND"]
        )

        # Minimum thresholds for meaningful analysis
        if len(source_countries) < 2:
            continue
        if len(topic_events) < 5:
            continue

        # Average tone per source country
        country_tones = {}
        for country in source_countries:
            country_events = [
                e for e in topic_events
                if e["source_country"] == country
            ]
            tones = [
                float(e["tone"]) for e in country_events
                if e.get("tone") is not None
            ]
            if tones:
                country_tones[country] = sum(tones) / len(tones)

        if len(country_tones) < 2:
            continue

        # Calculate synchronisation score
        # Low variance across country tones = high synchronisation
        tone_values = list(country_tones.values())
        mean_tone   = sum(tone_values) / len(tone_values)
        variance    = sum((t - mean_tone) ** 2 for t in tone_values) / len(tone_values)

        # Variance of 0 = perfect sync = score 1.0
        # Variance of 25+ = no sync = score 0.0
        sync_score = max(0.0, 1.0 - (variance / 25.0))

        # Boost if state media from non-India countries is involved
        state_media_involved = any(
            e["source_type"] == "state"
            for e in topic_events
            if e["source_country"] not in ["IND", "UNK"]
        )
        if state_media_involved:
            sync_score = min(1.0, sync_score * 1.3)

        # Threshold — below this is normal variation
        SYNC_THRESHOLD = 0.55
        if sync_score < SYNC_THRESHOLD:
            continue

        # Find which country is leading (most mentions)
        country_mention_counts = defaultdict(int)
        for e in topic_events:
            country_mention_counts[e["source_country"]] += int(e.get("mentions") or 1)
        leading_country = max(country_mention_counts, key=country_mention_counts.get)

        # Classify severity
        if sync_score >= 0.80:
            severity = "CRITICAL"
            explanation = "Extremely coordinated — state-level information operation likely"
        elif sync_score >= 0.65:
            severity = "HIGH"
            explanation = "Strong coordination across multiple countries media"
        else:
            severity = "MODERATE"
            explanation = "Unusual alignment detected — monitor closely"

        alerts.append({
            "type":                 "NARRATIVE_WARFARE",
            "topic":                f"{topic[0]} — {topic[1]}",
            "actor1":               topic[0],
            "actor2":               topic[1],
            "severity":             severity,
            "sync_score":           round(sync_score, 3),
            "event_count":          len(topic_events),
            "source_countries":     list(source_countries),
            "leading_country":      leading_country,
            "state_media_involved": state_media_involved,
            "mean_tone":            round(mean_tone, 2),
            "country_tones":        {k: round(v, 2) for k, v in country_tones.items()},
            "severity_explanation": explanation,
            "what_this_means": (
                f"Media from {len(source_countries)} countries is covering "
                f"{topic[0]}-{topic[1]} with unusually aligned tone "
                f"(sync score: {round(sync_score * 100)}%). "
                f"{'State media is involved. ' if state_media_involved else ''}"
                f"{leading_country} appears to be leading the narrative."
            )
        })

    # Sort by severity then sync score
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
    alerts.sort(key=lambda x: (severity_order.get(x["severity"], 3), -x["sync_score"]))

    logger.info(f"Narrative warfare: {len(alerts)} alerts detected")
    return alerts[:10]


# ═══════════════════════════════════════════════════════════════════
# USP 2: STRATEGIC BLIND SPOT DETECTOR
# ═══════════════════════════════════════════════════════════════════
#
# WHAT IT DETECTS:
# Events that are strategically important for India but are
# receiving very little media coverage. The gap between
# importance and coverage = the blind spot.
#
# HOW THE SCORE WORKS:
# Importance score (0-1) = weighted formula using:
#   - Who the actors are (tier-1 threats score higher)
#   - How hostile the event is (Goldstein magnitude)
#   - What type of event it is (military > diplomatic)
#   - Whether India is directly involved
#
# Coverage score (0-1) = normalised:
#   - NumMentions from GDELT
#   - NumSources from GDELT
#
# Blind spot score = importance - coverage
# High importance + low coverage = blind spot
# ═══════════════════════════════════════════════════════════════════

# Strategic weight per country (how much India cares)
COUNTRY_STRATEGIC_WEIGHT = {
    "CHINA":        1.0,
    "PAKISTAN":     1.0,
    "USA":          0.9,
    "RUSSIA":       0.8,
    "BANGLADESH":   0.7,
    "NEPAL":        0.7,
    "SRI LANKA":    0.7,
    "MALDIVES":     0.6,
    "MYANMAR":      0.6,
    "AFGHANISTAN":  0.5,
    "IRAN":         0.5,
}

# Severity weight per CAMEO event code
EVENT_SEVERITY_WEIGHT = {
    # Military — highest
    "131": 1.0,   # Threaten with military force
    "171": 1.0,   # Use conventional military force
    "172": 1.0,   # Use unconventional violence
    "201": 1.0,   # Conduct air strike
    "204": 1.0,   # Border conflict
    "062": 0.9,   # Military cooperation
    "063": 0.8,   # Joint military exercises
    # Economic
    "151": 0.8,   # Impose embargo
    "152": 0.8,   # Impose sanctions
    "057": 0.7,   # Sign agreement
    "061": 0.7,   # Economic cooperation
    "071": 0.7,   # Provide economic aid
    # Diplomatic
    "133": 0.8,   # Issue ultimatum
    "130": 0.7,   # Threaten (general)
    "120": 0.5,   # Reject
    "042": 0.5,   # Official visit
    "040": 0.4,   # Consult
}


def calculate_importance(event: dict) -> float:
    """Score strategic importance of one event for India (0 to 1)"""

    score = 0.0

    # Factor 1: Actor significance (35% weight)
    a1 = str(event.get("actor1") or "").upper()
    a2 = str(event.get("actor2") or "").upper()
    actor_score = max(
        COUNTRY_STRATEGIC_WEIGHT.get(a1, 0.3),
        COUNTRY_STRATEGIC_WEIGHT.get(a2, 0.3)
    )
    score += actor_score * 0.35

    # Factor 2: Hostility magnitude (35% weight)
    goldstein = abs(float(event.get("goldstein") or 0))
    score += min(goldstein / 10.0, 1.0) * 0.35

    # Factor 3: Event type severity (20% weight)
    event_code = str(event.get("event_code") or "")
    score += EVENT_SEVERITY_WEIGHT.get(event_code, 0.3) * 0.20

    # Factor 4: India directly involved (10% bonus)
    if any(term in a1 or term in a2 for term in ["IND", "INDIA"]):
        score += 0.10

    return min(score, 1.0)


def calculate_coverage(event: dict) -> float:
    """Normalise media coverage to 0-1 score"""

    mentions = float(event.get("mentions") or 0)
    sources  = float(event.get("sources")  or 0)

    # 100+ mentions = well covered, 1000+ = viral
    mention_score = min(mentions / 100.0, 1.0)
    # 20+ sources = well covered
    source_score  = min(sources  / 20.0,  1.0)

    return (mention_score + source_score) / 2.0


def explain_importance(event: dict) -> str:
    """Generate human-readable explanation of why an event is important"""

    parts = []
    a1 = str(event.get("actor1") or "").upper()
    a2 = str(event.get("actor2") or "").upper()

    if COUNTRY_STRATEGIC_WEIGHT.get(a1, 0) >= 0.8:
        parts.append(f"{event.get('actor1')} is a tier-1 strategic concern for India")
    if COUNTRY_STRATEGIC_WEIGHT.get(a2, 0) >= 0.8:
        parts.append(f"{event.get('actor2')} is a tier-1 strategic concern for India")

    goldstein = float(event.get("goldstein") or 0)
    if abs(goldstein) >= 7:
        direction = "severe conflict" if goldstein < 0 else "significant cooperation"
        parts.append(f"Goldstein score {goldstein} indicates {direction}")

    event_code = str(event.get("event_code") or "")
    if event_code in ["131", "171", "172", "201", "204"]:
        parts.append("Military event — direct security implications for India")
    elif event_code in ["151", "152"]:
        parts.append("Sanctions/embargo — economic security implications")
    elif event_code in ["057", "062"]:
        parts.append("Agreement or military cooperation — changes regional balance")

    return ". ".join(parts) if parts else "High strategic actor involvement detected"


def find_blind_spots(days_back: int = 7, top_n: int = 8) -> list[dict]:
    """
    Find strategically important events that are underreported.
    Returns blind spots ordered by gap between importance and coverage.
    """

    with get_driver().session() as session:
        result = session.run("""
            MATCH (e:Event)
            WHERE e.date >= toString(date() - duration({days: $days}))
            AND e.goldstein_score IS NOT NULL
            RETURN e.gdelt_id        AS id,
                   e.date            AS date,
                   e.actor1          AS actor1,
                   e.actor2          AS actor2,
                   e.event_code      AS event_code,
                   e.event_label     AS event_label,
                   e.goldstein_score AS goldstein,
                   e.num_mentions    AS mentions,
                   e.num_sources     AS sources,
                   e.location        AS location,
                   e.source_url      AS source_url,
                   e.article_title   AS headline
            ORDER BY e.date DESC
        """, days=days_back)
        events = [dict(r) for r in result]

    if not events:
        logger.info("No events found for blind spot analysis")
        return []

    blind_spots = []

    for event in events:
        importance = calculate_importance(event)
        coverage   = calculate_coverage(event)
        gap        = importance - coverage

        # Only flag if:
        # 1. Event is genuinely important (importance > 0.5)
        # 2. Coverage is significantly below importance (gap > 0.25)
        if importance < 0.5:
            continue
        if gap < 0.25:
            continue

        blind_spots.append({
            "type":             "BLIND_SPOT",
            "event_id":         str(event.get("id") or ""),
            "date":             str(event.get("date") or ""),
            "actor1":           str(event.get("actor1") or ""),
            "actor2":           str(event.get("actor2") or ""),
            "event_code":       str(event.get("event_code") or ""),
            "event_label":      str(event.get("event_label") or ""),
            "goldstein":        float(event.get("goldstein") or 0),
            "headline":         str(event.get("headline") or ""),
            "location":         str(event.get("location") or ""),
            "source_url":       str(event.get("source_url") or ""),
            "importance_score": round(importance, 3),
            "coverage_score":   round(coverage, 3),
            "blind_spot_score": round(gap, 3),
            "num_mentions":     int(event.get("mentions") or 0),
            "why_important":    explain_importance(event),
            "alert_message": (
                f"Strategic importance {round(importance * 10, 1)}/10 "
                f"but media coverage only {round(coverage * 10, 1)}/10. "
                f"Only {int(event.get('mentions') or 0)} articles worldwide covered this. "
                f"This event may be flying under the radar deliberately."
            )
        })

    blind_spots.sort(key=lambda x: x["blind_spot_score"], reverse=True)
    logger.info(f"Blind spots: {len(blind_spots[:top_n])} detected")
    return blind_spots[:top_n]


# ─── COMBINED ENTRY POINT ────────────────────────────────────────
# Called by /api/intelligence-alerts in main.py

def get_intelligence_alerts() -> dict:
    """
    Runs both USP analyses and returns combined results.
    This is the single function main.py calls.
    """
    narrative_alerts = detect_narrative_warfare(hours_back=48)
    blind_spots      = find_blind_spots(days_back=7)

    return {
        "narrative_warfare": narrative_alerts,
        "blind_spots":       blind_spots,
        "summary": {
            "narrative_alerts_count": len(narrative_alerts),
            "blind_spots_count":      len(blind_spots),
            "critical_count":         sum(
                1 for a in narrative_alerts
                if a.get("severity") == "CRITICAL"
            )
        }
    }