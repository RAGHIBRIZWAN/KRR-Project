import React, { useEffect, useState } from 'react';

const API_BASE = window.location.port === '5173' ? 'http://localhost:5000' : '';

const AssessmentLogin = () => {
  const [name, setName] = useState('');
  const [userId, setUserId] = useState('');
  const [toast, setToast] = useState(null);

  useEffect(() => {
    const savedName = localStorage.getItem('pi_name') || '';
    const savedId = localStorage.getItem('pi_userId') || '';
    if (savedName) setName(savedName);
    if (savedId) setUserId(savedId);
  }, []);

  const start = async () => {
    if (!name || !userId) {
      setToast({ type: 'info', msg: 'Please enter your name and ID' });
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/validate_user`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: userId, name: name }),
      });

      const data = await response.json();

      if (data.valid) {
        localStorage.setItem('pi_name', name);
        localStorage.setItem('pi_userId', userId);
        window.location.assign('/assessment/questions');
      } else {
        setToast({ type: 'error', msg: data.message });
      }
    } catch (error) {
      console.error("Validation error:", error);
      setToast({ type: 'error', msg: 'Connection error. Please try again.' });
    }
  };

  return (
    <div className="assessment-page">
      <div className="container single">
        <div className="login-card">
          <div className="logo">
            <div className="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="40" height="40">
                <path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10Zm-1.707-8.293-2-2a1 1 0 0 0-1.414 1.414l2.707 2.707a1 1 0 0 0 1.414 0l6-6a1 1 0 1 0-1.414-1.414L10.293 13.707Z" fill="currentColor" />
              </svg>
            </div>
            <p className="eyebrow">Step 1 · Identify</p>
            <h1>Big Five Personality Assessment</h1>
            <p className="subtitle">Start by telling us who you are. We keep your info local while you complete the 50 questions.</p>
          </div>

          <div className="form-group">
            <label>Your Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Enter your name" />
          </div>
          <div className="form-group">
            <label>User ID</label>
            <input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="Enter your ID" />
          </div>
          <button className="btn-primary" onClick={start} disabled={!name || !userId}>
            Start Assessment →
          </button>

          <div className="mini-steps">
            <div className="chip">Fast</div>
            <div className="chip">Private</div>
            <div className="chip">Research-backed</div>
          </div>
          <ul className="login-notes">
            <li>Your name and ID stay in your browser during the session.</li>
            <li>50 statements, 1–5 scale. Takes about 5 minutes.</li>
            <li>Results page shows scores, performance signals, and AI narrative.</li>
          </ul>
        </div>
      </div>

      <div className="toast-container">
        {toast && (
          <div className={`toast ${toast.type}`}>
            <span className="toast-icon">{toast.type === 'error' ? '❌' : toast.type === 'success' ? '✅' : 'ℹ️'}</span>
            <span className="toast-message">{toast.msg}</span>
            <button className="toast-close" onClick={() => setToast(null)}>×</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AssessmentLogin;
