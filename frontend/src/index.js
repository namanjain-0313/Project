// frontend/src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Global styles — resets and animations
const globalStyle = document.createElement('style');
globalStyle.textContent = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #010409; overflow: hidden; }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-8px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  @keyframes blink {
    50% { opacity: 0; }
  }
  
  /* Scrollbar styling */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: #0d1117; }
  ::-webkit-scrollbar-thumb { background: #30363d; }
`;
document.head.appendChild(globalStyle);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);