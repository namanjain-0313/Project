// frontend/src/components/EventFeed.jsx
// Live scrolling feed of recent geopolitical events
// Polls the backend every 60 seconds for new events

import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

function timeAgo(dateStr) {
  if (!dateStr) return '';
  // GDELT dates are YYYYMMDD format
  const clean = String(dateStr).replace(/[^0-9]/g, '').slice(0, 8);
  if (clean.length < 8) return dateStr;

  const year  = parseInt(clean.slice(0, 4));
  const month = parseInt(clean.slice(4, 6)) - 1;
  const day   = parseInt(clean.slice(6, 8));
  const date  = new Date(year, month, day);
  const now   = new Date();
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7)  return `${diffDays} days ago`;
  return `${Math.floor(diffDays / 7)}w ago`;
}

function hostilityBadge(score) {
  const s = parseFloat(score) || 0;
  if (s <= -7) return { label: 'CRITICAL', color: '#ef4444' };
  if (s <= -4) return { label: 'HOSTILE',  color: '#f97316' };
  if (s < 0)   return { label: 'TENSE',    color: '#fbbf24' };
  if (s === 0) return { label: 'NEUTRAL',  color: '#6b7280' };
  return { label: 'POSITIVE', color: '#22c55e' };
}

function EventCard({ event, isNew }) {
  const badge = hostilityBadge(event.goldstein);

  return (
    <div style={{
      ...styles.card,
      borderLeftColor: badge.color,
      animation: isNew ? 'slideIn 0.3s ease' : 'none'
    }}>
      <div style={styles.cardTop}>
        <span style={styles.actors}>
          {event.actor1 || '—'} → {event.actor2 || '—'}
        </span>
        <span style={{ ...styles.badge, color: badge.color }}>
          {badge.label}
        </span>
      </div>

      <div style={styles.headline}>
        {event.headline || event.event_type || 'Geopolitical event'}
      </div>

      <div style={styles.cardBottom}>
        <span style={styles.meta}>{event.event_type}</span>
        <span style={styles.meta}>{timeAgo(event.date)}</span>
        {event.source_url && (
          <a
            href={event.source_url}
            target="_blank"
            rel="noreferrer"
            style={styles.sourceLink}
          >
            Source ↗
          </a>
        )}
      </div>
    </div>
  );
}

export default function EventFeed() {
  const [events, setEvents]       = useState([]);
  const [newIds, setNewIds]       = useState(new Set());
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading]     = useState(true);
  const knownIds = useRef(new Set());

  const fetchEvents = () => {
    api.getLatestEvents(60)
      .then(data => {
        const incoming = data.events || [];

        // Find which ones are actually new
        const freshIds = new Set();
        incoming.forEach(e => {
          if (e.id && !knownIds.current.has(e.id)) {
            freshIds.add(e.id);
            knownIds.current.add(e.id);
          }
        });

        setEvents(incoming);
        setNewIds(freshIds);
        setLastUpdated(new Date());
        setLoading(false);

        // Clear new highlights after 3 seconds
        if (freshIds.size > 0) {
          setTimeout(() => setNewIds(new Set()), 3000);
        }
      })
      .catch(err => {
        console.error('Event feed error:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 60 * 1000); // every 60 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.headerTitle}>LIVE EVENT FEED</span>
        <span style={styles.liveIndicator}>
          <span style={styles.liveDot} />
          LIVE
        </span>
      </div>

      {lastUpdated && (
        <div style={styles.updateTime}>
          Updated {lastUpdated.toLocaleTimeString()}
        </div>
      )}

      {loading ? (
        <div style={styles.loading}>Loading events...</div>
      ) : (
        <div style={styles.feed}>
          {events.length === 0 ? (
            <div style={styles.empty}>No events yet. Database is loading.</div>
          ) : (
            events.map(event => (
              <EventCard
                key={event.id}
                event={event}
                isNew={newIds.has(event.id)}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    background: '#0d1117',
    border: '1px solid #21262d',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  header: {
    padding: '12px 16px',
    borderBottom: '1px solid #21262d',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0
  },
  headerTitle: {
    fontSize: 10,
    letterSpacing: 2,
    color: '#e8a020',
    fontFamily: 'monospace'
  },
  liveIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    fontSize: 9,
    color: '#22c55e',
    fontFamily: 'monospace'
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: '#22c55e',
    animation: 'pulse 2s infinite'
  },
  updateTime: {
    fontSize: 9,
    color: '#484f58',
    fontFamily: 'monospace',
    padding: '4px 16px',
    flexShrink: 0
  },
  feed: {
    overflowY: 'auto',
    flex: 1,
    padding: '8px 12px'
  },
  loading: {
    color: '#6b7280',
    fontFamily: 'monospace',
    fontSize: 12,
    padding: 16
  },
  empty: {
    color: '#484f58',
    fontFamily: 'monospace',
    fontSize: 11,
    padding: '20px 0'
  },
  card: {
    padding: '10px 12px',
    marginBottom: 8,
    borderLeft: '3px solid #6b7280',
    background: '#161b22',
    cursor: 'default'
  },
  cardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: 4
  },
  actors: {
    fontSize: 11,
    fontWeight: 600,
    color: '#c9d1d9',
    fontFamily: 'monospace'
  },
  badge: {
    fontSize: 8,
    letterSpacing: 1.5,
    fontFamily: 'monospace'
  },
  headline: {
    fontSize: 12,
    color: '#8b949e',
    lineHeight: 1.4,
    marginBottom: 6
  },
  cardBottom: {
    display: 'flex',
    gap: 10,
    alignItems: 'center'
  },
  meta: {
    fontSize: 9,
    color: '#484f58',
    fontFamily: 'monospace'
  },
  sourceLink: {
    fontSize: 9,
    color: '#3b82f6',
    fontFamily: 'monospace',
    textDecoration: 'none',
    marginLeft: 'auto'
  }
};
