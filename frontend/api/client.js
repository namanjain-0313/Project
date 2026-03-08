// frontend/src/api/client.js
// All API calls to the backend in one place.
// REACT_APP_API_URL is set in .env (local) or Vercel dashboard (production)

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function apiFetch(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} on ${path}`);
  }
  return response.json();
}

export const api = {

  // Latest events for the live feed panel
  getLatestEvents: (limit = 50) =>
    apiFetch(`/api/events/latest?limit=${limit}`),

  // Events for a specific country
  getCountryEvents: (country, limit = 30) =>
    apiFetch(`/api/events/country/${encodeURIComponent(country)}?limit=${limit}`),

  // Graph nodes + edges for the visualization
  getGraphData: () =>
    apiFetch('/api/graph'),

  // Risk scores for the gauge panel
  getRiskScores: () =>
    apiFetch('/api/risk-scores'),

  // Timeline data for trend chart
  getTimeline: (country, days = 30) =>
    apiFetch(`/api/timeline/${encodeURIComponent(country)}?days=${days}`),

  // Natural language Q&A
  askQuestion: (question) =>
    apiFetch('/api/query', {
      method: 'POST',
      body: JSON.stringify({ question })
    }),

  // Health check
  healthCheck: () =>
    apiFetch('/health'),

  // USP 1 + USP 2 combined — called by IntelligenceAlerts panel
  // Returns { narrative_warfare: [...], blind_spots: [...], summary: {...} }
  getIntelligenceAlerts: () =>
    apiFetch('/api/intelligence-alerts'),

  // USP 1 only — narrative warfare detection
  getNarrativeWarfare: () =>
    apiFetch('/api/narrative-warfare'),

  // USP 2 only — strategic blind spots
  getBlindSpots: () =>
    apiFetch('/api/blind-spots'),
};
