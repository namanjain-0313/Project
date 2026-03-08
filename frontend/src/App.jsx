// frontend/src/App.jsx
// Root layout — 4-panel dashboard + intelligence chat at bottom

import { useState, useEffect } from 'react';
import RiskScores          from './components/RiskScores';
import KnowledgeGraph      from './components/KnowledgeGraph';
import EventFeed           from './components/EventFeed';
import IntelligenceChat    from './components/IntelligenceChat';
import IntelligenceAlerts  from './components/IntelligenceAlerts';
import { api }             from './api/client';

export default function App() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    api.healthCheck()
      .then(d  => setStatus(d))
      .catch(() => setStatus({ status: 'offline' }));
  }, []);

  return (
    <div style={styles.root}>

      {/* ─── TOP BAR ─── */}
      <div style={styles.topBar}>
        <div style={styles.brand}>
          <span style={styles.brandDot} />
          GLOBAL ONTOLOGY ENGINE
          <span style={styles.brandSub}>India Strategic Intelligence</span>
        </div>

        <div style={styles.statusRow}>
          {status && (
            <>
              <span style={{
                ...styles.statusBadge,
                background: status.status === 'ok' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                color:      status.status === 'ok' ? '#22c55e'              : '#ef4444',
              }}>
                {status.status === 'ok' ? '● ONLINE' : '● OFFLINE'}
              </span>
              {status.chroma_events > 0 && (
                <span style={styles.eventCount}>
                  {status.chroma_events.toLocaleString()} events indexed
                </span>
              )}
            </>
          )}
          <span style={styles.updateNote}>GDELT updates every 15 min</span>
        </div>
      </div>

      {/* ─── MAIN GRID — 4 columns ─── */}
      <div style={styles.grid}>

        {/* Col 1: Risk scores */}
        <div style={styles.col}>
          <RiskScores />
        </div>

        {/* Col 2: Knowledge graph (widest) */}
        <div style={styles.col}>
          <KnowledgeGraph />
        </div>

        {/* Col 3: Live event feed */}
        <div style={styles.col}>
          <EventFeed />
        </div>

        {/* Col 4: Intelligence Alerts — USP 1 + USP 2 */}
        <div style={styles.col}>
          <IntelligenceAlerts />
        </div>

      </div>

      {/* ─── BOTTOM: Q&A Chat ─── */}
      <div style={styles.chatRow}>
        <IntelligenceChat />
      </div>

    </div>
  );
}

const styles = {
  root: {
    background: '#010409',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: 'monospace',
    color: '#c9d1d9',
  },
  topBar: {
    background: '#0d1117',
    borderBottom: '1px solid #21262d',
    padding: '10px 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0,
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    fontSize: 14,
    fontWeight: 700,
    letterSpacing: 2,
    color: '#f0f6fc',
  },
  brandDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: '#e8a020',
    display: 'inline-block',
  },
  brandSub: {
    fontSize: 9,
    color: '#6b7280',
    letterSpacing: 1,
    fontWeight: 400,
  },
  statusRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  statusBadge: {
    fontSize: 9,
    letterSpacing: 1.5,
    padding: '3px 8px',
    borderRadius: 2,
  },
  eventCount: {
    fontSize: 9,
    color: '#8b949e',
    letterSpacing: 1,
  },
  updateNote: {
    fontSize: 9,
    color: '#484f58',
    letterSpacing: 1,
  },
  // 4-column grid: risk | graph | feed | alerts
  grid: {
    display: 'grid',
    gridTemplateColumns: '200px 1fr 240px 250px',
    gap: 1,
    flex: '1 0 0',
    minHeight: 0,
    height: 'calc(60vh - 44px)',
  },
  col: {
    overflow: 'hidden',
    minHeight: 0,
  },
  chatRow: {
    height: '40vh',
    borderTop: '1px solid #21262d',
  },
};
