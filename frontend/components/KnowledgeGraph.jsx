// frontend/src/components/KnowledgeGraph.jsx
// Interactive force-directed graph showing entity relationships
// Uses react-force-graph-2d library

import { useState, useEffect, useCallback, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { api } from '../api/client';

// Node colors by entity type
const TYPE_COLORS = {
  COUNTRY:      '#3b82f6',  // blue
  PERSON:       '#a78bfa',  // purple
  ORGANIZATION: '#34d399',  // green
  LOCATION:     '#fbbf24',  // amber
  UNKNOWN:      '#6b7280',  // gray
};

// Edge colors by hostility score
function edgeColor(goldstein) {
  const score = parseFloat(goldstein) || 0;
  if (score <= -5) return '#ef4444';  // red — hostile
  if (score < 0)   return '#f97316';  // orange — tense
  return '#22c55e';                   // green — cooperative
}

export default function KnowledgeGraph({ onNodeSelect }) {
  const [graphData, setGraphData]   = useState({ nodes: [], links: [] });
  const [loading, setLoading]       = useState(true);
  const [selected, setSelected]     = useState(null);
  const graphRef = useRef();

  useEffect(() => {
    api.getGraphData()
      .then(data => {
        // react-force-graph wants "links" not "edges"
        const nodes = (data.nodes || []).map(n => ({
          id:    n.id,
          name:  n.name,
          type:  n.type || 'UNKNOWN',
          count: n.connection_count || 1,
          color: TYPE_COLORS[n.type] || TYPE_COLORS.UNKNOWN
        }));

        const links = (data.edges || []).map(e => ({
          source:    e.source,
          target:    e.target,
          label:     e.relation,
          goldstein: e.goldstein,
          color:     edgeColor(e.goldstein),
          date:      e.date
        }));

        setGraphData({ nodes, links });
        setLoading(false);
      })
      .catch(err => {
        console.error('Graph load error:', err);
        setLoading(false);
      });
  }, []);

  const handleNodeClick = useCallback(node => {
    setSelected(node);
    if (onNodeSelect) onNodeSelect(node);
    // Zoom to clicked node
    graphRef.current?.centerAt(node.x, node.y, 800);
    graphRef.current?.zoom(3, 800);
  }, [onNodeSelect]);

  if (loading) return (
    <div style={styles.container}>
      <div style={styles.loadingText}>Building knowledge graph...</div>
    </div>
  );

  return (
    <div style={styles.container}>
      {/* Legend */}
      <div style={styles.legend}>
        {Object.entries(TYPE_COLORS).filter(([k]) => k !== 'UNKNOWN').map(([type, color]) => (
          <span key={type} style={styles.legendItem}>
            <span style={{ ...styles.legendDot, background: color }} />
            {type}
          </span>
        ))}
      </div>

      {/* Edge legend */}
      <div style={styles.edgeLegend}>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendLine, background: '#ef4444' }} /> Hostile
        </span>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendLine, background: '#22c55e' }} /> Cooperative
        </span>
      </div>

      {/* Selected node info */}
      {selected && (
        <div style={styles.tooltip}>
          <div style={styles.tooltipName}>{selected.name}</div>
          <div style={styles.tooltipType}>{selected.type}</div>
          <div style={styles.tooltipCount}>{selected.count} connections</div>
        </div>
      )}

      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        backgroundColor="#0d1117"

        // Node appearance
        nodeColor={node => node.color}
        nodeRelSize={4}
        nodeVal={node => Math.max(1, Math.sqrt(node.count))}
        nodeLabel={node => `${node.name} (${node.type})`}
        onNodeClick={handleNodeClick}

        // Edge appearance
        linkColor={link => link.color}
        linkWidth={1}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkLabel={link => link.label}

        // Draw node labels
        nodeCanvasObject={(node, ctx, globalScale) => {
          const label = node.name;
          const fontSize = Math.max(8, 12 / globalScale);

          // Draw circle
          ctx.beginPath();
          ctx.arc(node.x, node.y, Math.max(2, Math.sqrt(node.count) * 2), 0, 2 * Math.PI);
          ctx.fillStyle = node.color;
          ctx.fill();

          // Draw label (only when zoomed in enough)
          if (globalScale >= 1.5) {
            ctx.font = `${fontSize}px monospace`;
            ctx.fillStyle = '#f0f6fc';
            ctx.textAlign = 'center';
            ctx.fillText(label, node.x, node.y + Math.sqrt(node.count) * 2 + fontSize);
          }
        }}
      />

      {/* Node count */}
      <div style={styles.stats}>
        {graphData.nodes.length} entities · {graphData.links.length} relationships
      </div>
    </div>
  );
}

const styles = {
  container: {
    background: '#0d1117',
    border: '1px solid #21262d',
    position: 'relative',
    height: '100%',
    overflow: 'hidden'
  },
  loadingText: {
    color: '#6b7280',
    fontFamily: 'monospace',
    fontSize: 12,
    padding: 20
  },
  legend: {
    position: 'absolute',
    top: 10,
    left: 10,
    display: 'flex',
    gap: 12,
    zIndex: 10,
    background: 'rgba(13,17,23,0.85)',
    padding: '6px 10px',
    borderRadius: 4
  },
  edgeLegend: {
    position: 'absolute',
    top: 40,
    left: 10,
    display: 'flex',
    gap: 12,
    zIndex: 10,
    background: 'rgba(13,17,23,0.85)',
    padding: '4px 10px',
    borderRadius: 4
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
    fontSize: 9,
    color: '#8b949e',
    fontFamily: 'monospace',
    letterSpacing: 0.5
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    display: 'inline-block'
  },
  legendLine: {
    width: 16,
    height: 2,
    display: 'inline-block',
    borderRadius: 1
  },
  tooltip: {
    position: 'absolute',
    top: 10,
    right: 10,
    background: 'rgba(13,17,23,0.95)',
    border: '1px solid #30363d',
    padding: '10px 14px',
    zIndex: 10,
    maxWidth: 200
  },
  tooltipName: {
    fontSize: 13,
    color: '#f0f6fc',
    fontWeight: 600,
    fontFamily: 'monospace'
  },
  tooltipType: {
    fontSize: 9,
    color: '#e8a020',
    letterSpacing: 2,
    fontFamily: 'monospace',
    marginTop: 2
  },
  tooltipCount: {
    fontSize: 10,
    color: '#6b7280',
    fontFamily: 'monospace',
    marginTop: 4
  },
  stats: {
    position: 'absolute',
    bottom: 10,
    right: 10,
    fontSize: 9,
    color: '#484f58',
    fontFamily: 'monospace',
    letterSpacing: 1
  }
};
