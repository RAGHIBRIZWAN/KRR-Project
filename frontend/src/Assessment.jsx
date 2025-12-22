import React, { useEffect, useState } from 'react';

const API_BASE = window.location.port === '5173' ? 'http://localhost:5000' : '';

const traitLabels = {
  Extraversion: '🌟 Extraversion',
  Neuroticism: '🧠 Emotional Stability',
  Agreeableness: '💚 Agreeableness',
  Conscientiousness: '🎯 Conscientiousness',
  Openness: '💡 Openness',
  Unknown: '❓ General'
};

const ratingChoices = [
  { value: 1, label: 'Strongly Disagree' },
  { value: 2, label: 'Disagree' },
  { value: 3, label: 'Neutral' },
  { value: 4, label: 'Agree' },
  { value: 5, label: 'Strongly Agree' }
];

const Assessment = () => {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [idx, setIdx] = useState(0);
  const [name, setName] = useState('');
  const [userId, setUserId] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingPrevious, setLoadingPrevious] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    const savedName = localStorage.getItem('pi_name');
    const savedId = localStorage.getItem('pi_userId');
    if (!savedName || !savedId) {
      window.location.assign('/assessment');
      return;
    }
    setName(savedName);
    setUserId(savedId);

    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/get_questions`);
        const data = await res.json();
        setQuestions(data || []);
      } catch (e) {
        setToast({ type: 'error', msg: 'Could not load questions. Is the server running?' });
      }
    };
    load();
  }, []);

  const current = questions[idx];
  const total = questions.length;

  const updateAnswer = (qid, val) => {
    setAnswers((prev) => ({ ...prev, [qid]: val }));
    if (idx < total - 1) setTimeout(() => setIdx((i) => i + 1), 200);
  };

  const submit = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/submit_assessment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, id: userId, answers })
      });
      const data = await res.json();
      localStorage.setItem('pi_result', JSON.stringify({ name, userId, result: data }));
      window.location.assign('/results');
    } catch (e) {
      setToast({ type: 'error', msg: 'Error calculating scores. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const restart = () => {
    setIdx(0);
    setAnswers({});
  };

  const loadPrevious = async () => {
    if (!userId) return;
    setLoadingPrevious(true);
    try {
      const res = await fetch(`${API_BASE}/get_previous_result?id=${encodeURIComponent(userId)}`);
      const data = await res.json();
      if (!res.ok) {
        setToast({ type: 'error', msg: data?.message || 'Could not load previous report.' });
      } else if (!data?.found) {
        setToast({ type: 'info', msg: data?.message || 'No previous report found for this ID.' });
      } else {
        localStorage.setItem('pi_result', JSON.stringify({ name, userId, result: data }));
        window.location.assign('/results');
      }
    } catch (e) {
      setToast({ type: 'error', msg: 'Could not load previous report.' });
    } finally {
      setLoadingPrevious(false);
    }
  };

  const progress = total ? Math.round(((idx + 1) / total) * 100) : 0;
  const answered = current && answers[current.id] !== undefined;
  const isLast = idx === total - 1;

  const renderQuestion = () => {
    if (!current) return null;
    return (
      <div className="question-wrapper">
        <span className="trait-badge">{traitLabels[current.trait] || current.trait}</span>
        <p className="question-text">{current.text}</p>
        <div className="rating-scale">
          {ratingChoices.map((choice) => (
            <div className="rating-option" key={choice.value}>
              <input
                type="radio"
                name={`q_${current.id}`}
                id={`q_${current.id}_${choice.value}`}
                value={choice.value}
                checked={answers[current.id] === choice.value}
                onChange={() => updateAnswer(current.id, choice.value)}
              />
              <label className="rating-label" htmlFor={`q_${current.id}_${choice.value}`}>
                <span className="rating-number">{choice.value}</span>
                <span className="rating-desc">{choice.label}</span>
              </label>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="assessment-page">
      <div className="container">
        <div className="login-card">
          <div className="logo">
            <div className="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="40" height="40">
                <path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10Zm-1.707-8.293-2-2a1 1 0 0 0-1.414 1.414l2.707 2.707a1 1 0 0 0 1.414 0l6-6a1 1 0 1 0-1.414-1.414L10.293 13.707Z" fill="currentColor" />
              </svg>
            </div>
            <h1>Question Session</h1>
            <p className="subtitle">Answer each statement honestly. Progress saves locally.</p>
          </div>
          <div className="participant">
            <div className="muted">Participant</div>
            <div className="participant-name">{name}</div>
            <div className="muted small">ID: {userId}</div>
          </div>
          <div className="progress-container" style={{ marginTop: 10 }}>
            <div className="progress-text">
              <span>Question {idx + 1} of {total || '?'} </span>
              <span>{progress}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
          <button className="btn-secondary" style={{ marginTop: 12 }} onClick={() => window.location.assign('/assessment')}>
            ← Change participant
          </button>
          <button className="btn-ghost" style={{ marginTop: 10 }} onClick={loadPrevious} disabled={!userId || loadingPrevious}>
            {loadingPrevious ? 'Loading previous report…' : 'See previous report'}
          </button>
        </div>

        {questions.length > 0 && (
          <div className="assessment-card" style={{ marginTop: 20 }}>
            <div id="question-container">{renderQuestion()}</div>

            <div className="nav-buttons">
              <button className="btn-secondary" onClick={() => setIdx((i) => Math.max(0, i - 1))} disabled={idx === 0}>
                ← Previous
              </button>
              <button className="btn-next" onClick={() => (isLast ? submit() : setIdx((i) => Math.min(total - 1, i + 1)))} disabled={!answered}>
                {isLast ? 'See Results →' : 'Next →'}
              </button>
            </div>
          </div>
        )}
      </div>

      {loading && (
        <div className="loading-overlay active">
          <div className="loading-spinner" />
          <div className="loading-text">Calculating your profile…</div>
          <div className="loading-subtext">Please wait a moment</div>
        </div>
      )}

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

export default Assessment;
