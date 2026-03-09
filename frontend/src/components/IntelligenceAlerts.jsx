// frontend/src/components/IntelligenceAlerts.jsx
// Shows USP 1 (Narrative Warfare) and USP 2 (Blind Spots) in one panel
// Two tabs — user can switch between them

import { useState, useEffect } from 'react';
import { api } from '../api/client';

// Severity colour mapping for narrative warfare cards
const SEVERITY_STYLE = {
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)',  border: '#ef4444' },
  HIGH:     { color: '#f97316', bg: 'rgba(249,115,22,0.08)', border: '#f97316' },
  MODERATE: { color: '#fbbf24', bg: 'rgba(251,191,36,0.08)', border: '#fbbf24' },
};


// ── Narrative Warfare Card ────────────────────────────────────────
function NarrativeCard({ alert }) {
  const [open, setOpen] = useState(false);
  const s = SEVERITY_STYLE[alert.severity] || SEVERITY_STYLE.MODERATE;

  return (
    <div
      onClick={() => setOpen(!open)}
      style={{ ...styles.card, borderLeftColor: s.border, background: s.bg, cursor: 'pointer' }}
    >
      {/* Header */}
      <div style={styles.cardHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13 }}>⚠️</span>
          <span style={{ ...styles.badge, color: s.color }}>{alert.severity}</span>
          <span style={styles.cardTitle}>
            {alert.actor1} — {alert.actor2}
          </span>
        </div>
        <span style={{ color: s.color, fontSize: 10, fontFamily: 'monospace', fontWeight: 700 }}>
          {Math.round(alert.sync_score * 100)}% sync
        </span>
      </div>

      {/* Summary line */}
      <div style={styles.cardSub}>
        {alert.event_count} events · {alert.source_countries.length} countries
        {alert.state_media_involved && (
          <span style={styles.stateBadge}>STATE MEDIA</span>
        )}
      </div>

      {/* Expanded detail */}
      {open && (
        <div style={styles.expanded}>
          <p style={styles.expandText}>{alert.what_this_means}</p>

          <div style={{ marginTop: 8 }}>
            <div style={styles.subLabel}>TONE BY COUNTRY</div>
            {Object.entries(alert.country_tones).map(([c, tone]) => (
              <div key={c} style={{ display: 'flex', gap: 8, marginBottom: 2 }}>
                <span style={{ ...styles.metaItem, width: 36 }}>{c}</span>
                <span style={{
                  fontSize: 10, fontFamily: 'monospace', fontWeight: 700,
                  color: tone < 0 ? '#ef4444' : '#22c55e'
                }}>
                  {tone > 0 ? '+' : ''}{tone}
                </span>
              </div>
            ))}
          </div>

          <div style={{ ...styles.subLabel, marginTop: 8 }}>
            LEADING: {alert.leading_country}
          </div>
        </div>
      )}
    </div>
  );
}


// ── Blind Spot Card ───────────────────────────────────────────────
function BlindSpotCard({ spot }) {
  const [open, setOpen] = useState(false);

  const impPct = Math.round(spot.importance_score * 100);
  const covPct = Math.round(spot.coverage_score   * 100);

  return (
    <div
      onClick={() => setOpen(!open)}
      style={{ ...styles.card, borderLeftColor: '#a78bfa', background: 'rgba(167,139,250,0.05)', cursor: 'pointer' }}
    >
      {/* Header */}
      <div style={styles.cardHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13 }}>🔍</span>
          <span style={{ ...styles.badge, color: '#a78bfa' }}>BLIND SPOT</span>
          <span style={styles.cardTitle}>
            {spot.actor1} — {spot.actor2}
          </span>
        </div>
        <span style={{ color: '#a78bfa', fontSize: 10, fontFamily: 'monospace' }}>
          Gap: {Math.round(spot.blind_spot_score * 100)}
        </span>
      </div>

      {/* Headline */}
      <div style={styles.cardSub}>
        {spot.headline || spot.event_label || 'Geopolitical event'}
      </div>

      {/* Importance vs Coverage bars — always visible */}
      <div style={{ marginTop: 8 }}>
        {[
          { label: 'Importance', pct: impPct, color: '#a78bfa' },
          { label: 'Coverage',   pct: covPct, color: '#6b7280' },
        ].map(({ label, pct, color }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <span style={{ ...styles.metaItem, width: 60 }}>{label}</span>
            <div style={styles.barTrack}>
              <div style={{ ...styles.barFill, width: `${pct}%`, background: color }} />
            </div>
            <span style={{ ...styles.metaItem, width: 20, textAlign: 'right' }}>{pct}</span>
          </div>
        ))}
      </div>

      {/* Expanded detail */}
      {open && (
        <div style={styles.expanded}>
          <p style={styles.expandText}>{spot.alert_message}</p>
          <p style={{ ...styles.expandText, color: '#a78bfa', marginTop: 6 }}>
            {spot.why_important}
          </p>
          <div style={{ display: 'flex', gap: 10, marginTop: 8, alignItems: 'center' }}>
            <span style={styles.metaItem}>Goldstein: {spot.goldstein}</span>
            <span style={styles.metaItem}>Mentions: {spot.num_mentions}</span>
            {spot.source_url && (
              <a
                href={spot.source_url}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: 9, color: '#3b82f6', fontFamily: 'monospace', marginLeft: 'auto' }}
                onClick={e => e.stopPropagation()}
              >
                Source ↗
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


// ── Main Component ────────────────────────────────────────────────
export default function IntelligenceAlerts() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab]         = useState('narrative'); // 'narrative' | 'blindspots'

  useEffect(() => {
    const load = () => {
      api.getIntelligenceAlerts()
        .then(d  => { setData(d); setLoading(false); })
        .catch(() => setLoading(false));
    };
    load();
    // Same 15-min cadence as GDELT scheduler
    const t = setInterval(load, 15 * 60 * 1000);
    return () => clearInterval(t);
  }, []);

  const narrativeAlerts = data?.narrative_warfare || [];
  const blindSpots      = data?.blind_spots       || [];
  const criticalCount   = data?.summary?.critical_count || 0;

  return (
    <div style={styles.container}>

      {/* Header */}
      <div style={styles.header}>
        <span style={styles.headerTitle}>INTELLIGENCE ALERTS</span>
        {criticalCount > 0 && (
          <span style={styles.criticalBadge}>{criticalCount} CRITICAL</span>
        )}
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        <button
          style={{
            ...styles.tab,
            color:            tab === 'narrative'  ? '#e8a020' : '#6b7280',
            borderBottomColor: tab === 'narrative' ? '#e8a020' : 'transparent',
          }}
          onClick={() => setTab('narrative')}
        >
          ⚠️ Narrative ({narrativeAlerts.length})
        </button>
        <button
          style={{
            ...styles.tab,
            color:            tab === 'blindspots'  ? '#a78bfa' : '#6b7280',
            borderBottomColor: tab === 'blindspots' ? '#a78bfa' : 'transparent',
          }}
          onClick={() => setTab('blindspots')}
        >
          🔍 Blind Spots ({blindSpots.length})
        </button>
      </div>

      {/* Content */}
      <div style={styles.content}>
        {loading ? (
          <div style={styles.msg}>Scanning for threats...</div>
        ) : tab === 'narrative' ? (
          narrativeAlerts.length === 0
            ? <div style={styles.msg}>No coordinated narratives detected in last 48h</div>
            : narrativeAlerts.map((a, i) => <NarrativeCard key={i} alert={a} />)
        ) : (
          blindSpots.length === 0
            ? <div style={styles.msg}>No strategic blind spots detected this week</div>
            : blindSpots.map((s, i) => <BlindSpotCard key={i} spot={s} />)
        )}
      </div>
    </div>
  );
}


// ── Styles ────────────────────────────────────────────────────────
const styles = {
  container: {
    background: '#0d1117',
    border: '1px solid #21262d',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden',
  },
  header: {
    padding: '12px 16px',
    borderBottom: '1px solid #21262d',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0,
  },
  headerTitle: {
    fontSize: 10,
    letterSpacing: 2,
    color: '#e8a020',
    fontFamily: 'monospace',
  },
  criticalBadge: {
    fontSize: 8,
    letterSpacing: 1.5,
    color: '#ef4444',
    background: 'rgba(239,68,68,0.1)',
    padding: '2px 8px',
    fontFamily: 'monospace',
  },
  tabs: {
    display: 'flex',
    borderBottom: '1px solid #21262d',
    flexShrink: 0,
  },
  tab: {
    flex: 1,
    padding: '8px 4px',
    background: 'none',
    border: 'none',
    borderBottom: '2px solid transparent',
    fontSize: 10,
    fontFamily: 'monospace',
    cursor: 'pointer',
    letterSpacing: 0.3,
  },
  content: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px 10px',
  },
  msg: {
    color: '#484f58',
    fontSize: 11,
    fontFamily: 'monospace',
    padding: '16px 0',
    fontStyle: 'italic',
  },
  card: {
    padding: '10px 10px',
    marginBottom: 8,
    borderLeft: '3px solid',
    borderRadius: '0 2px 2px 0',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  badge: {
    fontSize: 8,
    letterSpacing: 1.5,
    fontFamily: 'monospace',
  },
  cardTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: '#c9d1d9',
    fontFamily: 'monospace',
  },
  cardSub: {
    fontSize: 10,
    color: '#8b949e',
    fontFamily: 'monospace',
    lineHeight: 1.4,
  },
  stateBadge: {
    marginLeft: 8,
    fontSize: 7,
    letterSpacing: 1,
    color: '#ef4444',
    border: '1px solid #ef4444',
    padding: '1px 4px',
    fontFamily: 'monospace',
  },
  expanded: {
    marginTop: 10,
    paddingTop: 10,
    borderTop: '1px solid rgba(255,255,255,0.05)',
  },
  expandText: {
    fontSize: 10,
    color: '#8b949e',
    lineHeight: 1.6,
    fontFamily: 'monospace',
  },
  subLabel: {
    fontSize: 8,
    letterSpacing: 1.5,
    color: '#484f58',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  metaItem: {
    fontSize: 9,
    color: '#484f58',
    fontFamily: 'monospace',
  },
  barTrack: {
    flex: 1,
    height: 4,
    background: '#21262d',
    borderRadius: 2,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 2,
    transition: 'width 0.4s ease',
  },
};
