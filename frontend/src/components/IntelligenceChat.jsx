// frontend/src/components/IntelligenceChat.jsx
// Natural language Q&A powered by RAG + Claude

import { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';

const EXAMPLE_QUESTIONS = [
  "What military actions has China taken near India in the last 7 days?",
  "What is the current status of India-Pakistan relations?",
  "How is the China-Pakistan Economic Corridor affecting India?",
  "What happened at the LAC recently?",
  "What are the latest India-US diplomatic developments?"
];

function Message({ msg }) {
  if (msg.role === 'user') {
    return (
      <div style={styles.userMsg}>
        <span style={styles.userLabel}>ANALYST</span>
        <div style={styles.userText}>{msg.content}</div>
      </div>
    );
  }

  return (
    <div style={styles.aiMsg}>
      <span style={styles.aiLabel}>GOE INTELLIGENCE</span>
      <div style={styles.aiText}>
        {/* Render markdown-ish bold text */}
        {msg.content.split('\n').map((line, i) => (
          <p key={i} style={{ margin: '4px 0', lineHeight: 1.6 }}>
            {line.startsWith('**') && line.includes('**', 2) ? (
              <strong style={{ color: '#e8a020' }}>
                {line.replace(/\*\*/g, '')}
              </strong>
            ) : line}
          </p>
        ))}
      </div>
      {msg.sources && msg.sources.length > 0 && (
        <div style={styles.sources}>
          <span style={styles.sourcesLabel}>SOURCES</span>
          {msg.sources.slice(0, 3).map((url, i) => (
            <a key={i} href={url} target="_blank" rel="noreferrer" style={styles.sourceUrl}>
              [{i+1}] {new URL(url).hostname} ↗
            </a>
          ))}
        </div>
      )}
      {msg.events_searched > 0 && (
        <div style={styles.searchedCount}>
          Searched {msg.events_searched} events in knowledge base
        </div>
      )}
    </div>
  );
}

export default function IntelligenceChat() {
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState('');
  const [loading, setLoading]     = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendQuestion = async (question) => {
    const q = question || input.trim();
    if (!q || loading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setLoading(true);

    try {
      const result = await api.askQuestion(q);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.answer,
        sources: result.sources || [],
        events_searched: result.events_searched || 0
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Intelligence service unavailable. Please try again.',
        sources: []
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.headerTitle}>INTELLIGENCE BRIEF</span>
        <span style={styles.headerSub}>RAG-powered · Grounded in live data</span>
      </div>

      {/* Example questions */}
      {messages.length === 0 && (
        <div style={styles.examples}>
          <div style={styles.examplesLabel}>SUGGESTED QUERIES</div>
          {EXAMPLE_QUESTIONS.map((q, i) => (
            <button key={i} style={styles.exampleBtn} onClick={() => sendQuestion(q)}>
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div style={styles.messages}>
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}

        {loading && (
          <div style={styles.aiMsg}>
            <span style={styles.aiLabel}>GOE INTELLIGENCE</span>
            <div style={styles.analyzing}>
              Analyzing knowledge graph
              <span style={styles.dots}>...</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendQuestion()}
          placeholder="Ask about any geopolitical situation..."
          disabled={loading}
        />
        <button
          style={{
            ...styles.sendBtn,
            opacity: loading || !input.trim() ? 0.4 : 1
          }}
          onClick={() => sendQuestion()}
          disabled={loading || !input.trim()}
        >
          →
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    background: '#0d1117',
    border: '1px solid #21262d',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden'
  },
  header: {
    padding: '12px 16px',
    borderBottom: '1px solid #21262d',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    flexShrink: 0
  },
  headerTitle: {
    fontSize: 10,
    letterSpacing: 2,
    color: '#e8a020',
    fontFamily: 'monospace'
  },
  headerSub: {
    fontSize: 9,
    color: '#484f58',
    fontFamily: 'monospace'
  },
  examples: {
    padding: '12px 16px',
    borderBottom: '1px solid #21262d',
    flexShrink: 0
  },
  examplesLabel: {
    fontSize: 8,
    letterSpacing: 2,
    color: '#484f58',
    fontFamily: 'monospace',
    marginBottom: 8
  },
  exampleBtn: {
    display: 'block',
    width: '100%',
    textAlign: 'left',
    background: 'none',
    border: 'none',
    padding: '5px 0',
    fontSize: 11,
    color: '#3b82f6',
    cursor: 'pointer',
    fontFamily: 'monospace',
    lineHeight: 1.4
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '12px 16px'
  },
  userMsg: {
    marginBottom: 16
  },
  userLabel: {
    fontSize: 8,
    letterSpacing: 2,
    color: '#6b7280',
    fontFamily: 'monospace',
    display: 'block',
    marginBottom: 4
  },
  userText: {
    fontSize: 13,
    color: '#c9d1d9',
    fontFamily: 'monospace',
    background: '#161b22',
    padding: '8px 12px',
    lineHeight: 1.5
  },
  aiMsg: {
    marginBottom: 20
  },
  aiLabel: {
    fontSize: 8,
    letterSpacing: 2,
    color: '#e8a020',
    fontFamily: 'monospace',
    display: 'block',
    marginBottom: 6
  },
  aiText: {
    fontSize: 12,
    color: '#8b949e',
    lineHeight: 1.7,
    fontFamily: 'monospace'
  },
  analyzing: {
    fontSize: 11,
    color: '#6b7280',
    fontFamily: 'monospace',
    fontStyle: 'italic'
  },
  dots: {
    animation: 'blink 1s step-start infinite'
  },
  sources: {
    marginTop: 10,
    paddingTop: 8,
    borderTop: '1px solid #21262d'
  },
  sourcesLabel: {
    fontSize: 8,
    letterSpacing: 2,
    color: '#484f58',
    fontFamily: 'monospace',
    display: 'block',
    marginBottom: 4
  },
  sourceUrl: {
    fontSize: 10,
    color: '#3b82f6',
    fontFamily: 'monospace',
    display: 'block',
    textDecoration: 'none',
    marginBottom: 2,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap'
  },
  searchedCount: {
    fontSize: 9,
    color: '#484f58',
    fontFamily: 'monospace',
    marginTop: 6
  },
  inputRow: {
    display: 'flex',
    gap: 8,
    padding: '12px 16px',
    borderTop: '1px solid #21262d',
    flexShrink: 0
  },
  input: {
    flex: 1,
    background: '#161b22',
    border: '1px solid #30363d',
    padding: '8px 12px',
    fontSize: 12,
    color: '#c9d1d9',
    fontFamily: 'monospace',
    outline: 'none'
  },
  sendBtn: {
    background: '#e8a020',
    border: 'none',
    color: '#0d1117',
    padding: '8px 16px',
    fontSize: 16,
    cursor: 'pointer',
    fontWeight: 'bold'
  }
};
