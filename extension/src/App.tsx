import { useState, useEffect } from 'react';
import { MemoryRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

// Declare Puter globally
declare const puter: any;

function DashboardHome() {
  const [status, setStatus] = useState('في وضع الاستعداد (Sleeping)');
  const [aiTest, setAiTest] = useState('');

  useEffect(() => {
    // Ping Puter.js to test connection
    if (typeof puter !== 'undefined') {
      puter.ai.chat('Say "Swarm AI Online"').then((res: any) => {
        setAiTest(res.message?.content || res);
      }).catch((e: any) => setAiTest('فشل في الاتصال بمحرك الذكاء الاصطناعي'));
    }
  }, []);

  const startSwarmProtocol = async () => {
    setStatus('جاري مسح صفحة LinkedIn...');
    
    // Fallback for when running outside of Chrome Extension environment (like dev server)
    if (typeof chrome === 'undefined' || !chrome.tabs) {
      console.warn("Not running in an extension context.");
      setStatus('وضع المطور: مسح وهمي');
      return;
    }

    // Query the active tab and send a message to the injected content script
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.id) {
      chrome.tabs.sendMessage(tab.id, { action: "START_SWARM" }, (response) => {
        if (chrome.runtime.lastError) {
          setStatus('خطأ: يرجى فتح LinkedIn أولاً.');
          console.error(chrome.runtime.lastError);
        } else if (response && response.status === "running") {
          setStatus('السرب نشط! جاري التقديم...');
        }
      });
    }
  };

  return (
                </svg>
                Discord
              </a>
            </li>
            <li>
              <a href="https://x.com/vite_js" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#x-icon"></use>
                </svg>
                X.com
              </a>
            </li>
            <li>
              <a href="https://bsky.app/profile/vite.dev" target="_blank">
                <svg
    <div className="dashboard-container">
      <h1>JobHunt Pro - Swarm Agent</h1>
      <div className="status-box">
        <p>Agent Status: <span className="status-text">{status}</span></p>
        <p>AI Engine: <span className="ai-text">{aiTest || 'Loading Puter.js...'}</span></p>
      </div>
      <button onClick={startSwarmProtocol}>Start Swarm Protocol</button>
    </div>
  );
}

export default App;
