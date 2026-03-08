// frontend/src/components/RiskScores.jsx
// Shows hostility/cooperation score for each of India's key relationships

import { useState, useEffect } from 'react';
import { api } from '../api/client';

// Color based on Goldstein score (-10 to +10)
function scoreColor(score) {
  if (score <= -5) return '#ef4444';   // red — very hostile
  if (score < 0)   return '#f97316';   // orange — hostile
  if (score === 0) return '#6b7280';   // gray — neutral
  if (score < 5)   return '#84cc16';   // light green — cooperative
  return '#22c55e';                     // green — very cooperative
}

function scoreLabel(score) {
  if (score <= -7) return 'CRITICAL';
  if (score <= -4) return 'HOSTILE';
  if (score < 0)   return 'TENSE';
  if (score === 0) return 'NEUTRAL';
  if (score < 5)   return 'STABLE';
  return 'COOPERATIVE';
}

export default function RiskScores() {
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = () => {
      api.getRiskScores()
        .then(data => {
          setScores(data.scores || []);
          setLoading(false);
        })
        .catch(err => {
          console.error('Risk scores error:', err);
          setLoading(false);
        });
    };

    fetch();
    const interval = setInterval(fetch, 5 * 60 * 1000); // refresh every 5 mins
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div style={styles.container}>
      <div style={styles.header}>RELATIONSHIP STATUS</div>
      <div style={styles.loading}>Loading...</div>
    </div>
  );

  return (
    <div style={styles.container}>
      <div style={styles.header}>RELATIONSHIP STATUS — INDIA</div>
      <div style={styles.subtitle}>14-day average hostility index</div>

      {scores.map(item => {
        const barWidth = Math.min(Math.abs(item.avg_score) / 10 * 100, 100);
        const color = scoreColor(item.avg_score);

        return (
          <div key={item.country} style={styles.row}>
            <div style={styles.countryName}>{item.country}</div>

            <div style={styles.barTrack}>
              <div style={{
                ...styles.bar,
                width: `${barWidth}%`,
                backgroundColor: color
              }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 3 }}>
              <span style={{ ...styles.label, color }}>
                {scoreLabel(item.avg_score)}
              </span>
              <span style={styles.score}>
                {item.avg_score > 0 ? '+' : ''}{item.avg_score}
              </span>
            </div>

            <div style={styles.eventCount}>
              {item.event_count} events tracked
            </div>
          </div>
        );
      })}
    </div>
  );
}

const styles = {
  container: {
    background: '#0d1117',
    border: '1px solid #21262d',
    padding: '16px',
    height: '100%'
  },
  header: {
    fontSize: 10,
    letterSpacing: 2,
    color: '#e8a020',
    fontFamily: 'monospace',
    marginBottom: 4
  },
  subtitle: {
    fontSize: 10,
    color: '#6b7280',
    fontFamily: 'monospace',
    marginBottom: 16
  },
  loading: {
    color: '#6b7280',
    fontSize: 12,
    fontFamily: 'monospace'
  },
  row: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottom: '1px solid #21262d'
  },
  countryName: {
    fontSize: 13,
    fontWeight: 600,
    color: '#f0f6fc',
    marginBottom: 6,
    fontFamily: 'monospace'
  },
  barTrack: {
    background: '#21262d',
    height: 6,
    borderRadius: 3,
    overflow: 'hidden'
  },
  bar: {
    height: '100%',
    borderRadius: 3,
    transition: 'width 0.5s ease'
  },
  label: {
    fontSize: 9,
    letterSpacing: 1.5,
    fontFamily: 'monospace'
  },
  score: {
    fontSize: 10,
    color: '#8b949e',
    fontFamily: 'monospace'
  },
  eventCount: {
    fontSize: 9,
    color: '#484f58',
    fontFamily: 'monospace',
    marginTop: 2
  }
};
