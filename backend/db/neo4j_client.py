# backend/db/neo4j_client.py
# All Neo4j operations — loading events and querying for the API

import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.environ["NEO4J_URL"],
            auth=(
                os.environ.get("NEO4J_USERNAME", "neo4j"),
                os.environ["NEO4J_PASSWORD"]
            )
        )
        logger.info("Connected to Neo4j")
    return _driver


def test_connection() -> bool:
    try:
        with get_driver().session() as session:
            session.run("RETURN 1")
        return True
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
        return False


# ─── WRITE OPERATIONS ────────────────────────────────────────────


def save_event(processed_event: dict, resolved_triples: list[dict]):
    """
    Save a fully processed event into Neo4j.
    Creates Entity nodes and RELATION edges.
    Uses MERGE so we never create duplicate nodes.
    """
    with get_driver().session() as session:

        # Save the raw event node first
        session.run("""
            MERGE (e:Event {gdelt_id: $gdelt_id})
            SET e.date            = $date,
                e.actor1          = $actor1,
                e.actor2          = $actor2,
                e.event_label     = $event_label,
                e.goldstein_score = $goldstein_score,
                e.avg_tone        = $avg_tone,
                e.num_mentions    = $num_mentions,
                e.location        = $location,
                e.source_url      = $source_url,
                e.article_title   = $article_title
        """,
            gdelt_id        = processed_event['gdelt_id'],
            date            = str(processed_event['date']),
            actor1          = processed_event['actor1'],
            actor2          = processed_event['actor2'],
            event_label     = processed_event['event_label'],
            goldstein_score = processed_event['goldstein_score'],
            avg_tone        = processed_event['avg_tone'],
            num_mentions    = processed_event['num_mentions'],
            location        = processed_event['location'],
            source_url      = processed_event['source_url'],
            article_title   = processed_event['article_title']
        )

        # Save each triple as Entity → RELATION → Entity
        for triple in resolved_triples:
            subject = triple['subject_resolved']
            obj     = triple['object_resolved']

            # Create/update subject entity node
            session.run("""
                MERGE (s:Entity {canonical_name: $name})
                SET s.wikidata_id = $wikidata_id,
                    s.type        = $type
            """,
                name        = subject['canonical_name'],
                wikidata_id = subject.get('wikidata_id', ''),
                type        = subject['type']
            )

            # Create/update object entity node
            session.run("""
                MERGE (o:Entity {canonical_name: $name})
                SET o.wikidata_id = $wikidata_id,
                    o.type        = $type
            """,
                name        = obj['canonical_name'],
                wikidata_id = obj.get('wikidata_id', ''),
                type        = obj['type']
            )

            # Create the relationship edge
            session.run("""
                MATCH (s:Entity {canonical_name: $subject_name})
                MATCH (o:Entity {canonical_name: $object_name})
                CREATE (s)-[r:RELATION {
                    type:            $relation_type,
                    date:            $date,
                    goldstein_score: $goldstein,
                    confidence:      $confidence,
                    source_url:      $source_url,
                    quote:           $quote,
                    gdelt_id:        $gdelt_id
                }]->(o)
            """,
                subject_name  = subject['canonical_name'],
                object_name   = obj['canonical_name'],
                relation_type = triple['relation'],
                date          = str(processed_event['date']),
                goldstein     = processed_event['goldstein_score'],
                confidence    = triple.get('confidence', 0.8),
                source_url    = processed_event['source_url'],
                quote         = triple.get('quote', ''),
                gdelt_id      = processed_event['gdelt_id']
            )


# ─── READ OPERATIONS (used by FastAPI endpoints) ─────────────────


def get_latest_events(limit: int = 50) -> list[dict]:
    """Return the most recent events, ordered by date"""
    with get_driver().session() as session:
        result = session.run("""
            MATCH (e:Event)
            WHERE e.date IS NOT NULL
            RETURN e.gdelt_id        AS id,
                   e.date            AS date,
                   e.actor1          AS actor1,
                   e.actor2          AS actor2,
                   e.event_label     AS event_type,
                   e.goldstein_score AS goldstein,
                   e.num_mentions    AS mentions,
                   e.location        AS location,
                   e.source_url      AS source_url,
                   e.article_title   AS headline
            ORDER BY e.date DESC
            LIMIT $limit
        """, limit=limit)

        return [dict(record) for record in result]


def get_graph_data() -> dict:
    """
    Return nodes and edges for the frontend graph visualization.
    Returns top entities by number of relationships.
    """
    with get_driver().session() as session:

        # Get top 80 most connected entities
        nodes_result = session.run("""
            MATCH (e:Entity)
            OPTIONAL MATCH (e)-[r]-()
            RETURN e.canonical_name AS id,
                   e.canonical_name AS name,
                   e.type           AS type,
                   e.wikidata_id    AS wikidata_id,
                   count(r)         AS connection_count
            ORDER BY connection_count DESC
            LIMIT 80
        """)
        nodes = [dict(r) for r in nodes_result]

        # Get edges between those top entities
        node_names = [n['id'] for n in nodes]
        edges_result = session.run("""
            MATCH (s:Entity)-[r:RELATION]->(o:Entity)
            WHERE s.canonical_name IN $names AND o.canonical_name IN $names
            RETURN s.canonical_name  AS source,
                   o.canonical_name  AS target,
                   r.type            AS relation,
                   r.date            AS date,
                   r.goldstein_score AS goldstein,
                   r.source_url      AS source_url
            ORDER BY r.date DESC
            LIMIT 300
        """, names=node_names)
        edges = [dict(r) for r in edges_result]

        return {"nodes": nodes, "edges": edges}


def get_risk_scores() -> list[dict]:
    """
    Compute risk score for each strategic country.
    Score = average Goldstein score of events in last 14 days.
    Lower (more negative) = more hostile toward India.
    """
    with get_driver().session() as session:
        countries = ["China", "Pakistan", "United States", "Russia", "Bangladesh"]
        scores = []

        for country in countries:
            result = session.run("""
                MATCH (e:Event)
                WHERE (e.actor1 CONTAINS $country OR e.actor2 CONTAINS $country)
                  AND e.date >= toString(date() - duration({days: 14}))
                RETURN avg(e.goldstein_score) AS avg_score,
                       count(e)               AS event_count,
                       min(e.goldstein_score) AS min_score,
                       max(e.goldstein_score) AS max_score
            """, country=country)

            record = result.single()
            scores.append({
                "country":     country,
                "avg_score":   round(float(record["avg_score"]  or 0), 2),
                "event_count": int(record["event_count"]         or 0),
                "min_score":   round(float(record["min_score"]   or 0), 2),
                "max_score":   round(float(record["max_score"]   or 0), 2),
            })

        return scores


def get_timeline(country: str, days: int = 30) -> list[dict]:
    """Return daily aggregated hostility scores for a country over time"""
    with get_driver().session() as session:
        result = session.run("""
            MATCH (e:Event)
            WHERE (e.actor1 CONTAINS $country OR e.actor2 CONTAINS $country)
              AND e.date >= toString(date() - duration({days: $days}))
            RETURN e.date                 AS date,
                   avg(e.goldstein_score) AS avg_hostility,
                   count(e)              AS num_events
            ORDER BY e.date ASC
        """, country=country, days=days)

        return [dict(r) for r in result]


def get_events_for_country(country: str, limit: int = 30) -> list[dict]:
    """Return recent events involving a specific country"""
    with get_driver().session() as session:
        result = session.run("""
            MATCH (e:Event)
            WHERE e.actor1 CONTAINS $country OR e.actor2 CONTAINS $country
            RETURN e.gdelt_id        AS id,
                   e.date            AS date,
                   e.actor1          AS actor1,
                   e.actor2          AS actor2,
                   e.event_label     AS event_type,
                   e.goldstein_score AS goldstein,
                   e.article_title   AS headline,
                   e.source_url      AS source_url
            ORDER BY e.date DESC
            LIMIT $limit
        """, country=country, limit=limit)

        return [dict(r) for r in result]