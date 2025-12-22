import React, { useEffect, useState } from 'react';

const Results = () => {
  const [payload, setPayload] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('pi_result');
    if (stored) {
      try {
        setPayload(JSON.parse(stored));
      } catch (e) {
        setPayload(null);
      }
    }
  }, []);

  if (!payload) {
    return (
      <div className="page">
        <main className="shell">
          <section className="panel hero" style={{ marginTop: 24 }}>
            <p className="eyebrow">Results</p>
            <h1>No results yet</h1>
            <p className="lede">Run an assessment first, then your latest scores will appear here.</p>
            <div className="actions">
              <a className="btn primary" href="/assessment">Start assessment</a>
              <a className="btn ghost" href="/">Back to landing</a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  const { name, userId, result } = payload;
  const scores = result?.scores || {};
  const performance = result?.performance || {};

  return (
    <div className="page">
      <main className="shell">
        <section className="panel hero" style={{ marginTop: 24 }}>
          <div className="hero-topline">
            <div>
              <p className="eyebrow">Results</p>
              <h1>Your personality insights</h1>
              <p className="lede">Hi {name}, here are the findings for ID {userId}.</p>
            </div>
            <div className="pill">Completed</div>
          </div>
          <div className="actions">
            <a className="btn primary" href="/assessment">Retake assessment</a>
            <a className="btn ghost" href="/">Back to landing</a>
          </div>
        </section>

        <section className="panel results-grid">
          <div className="card wide">
            <div className="section-header">
              <div className="pill">Trait scores</div>
              <div className="muted small">Percent scales by trait</div>
            </div>
            <div className="scores-grid">
              {Object.entries(scores).map(([trait, score]) => (
                <div className="score-item" key={trait}>
                  <div className="score-trait">{trait}</div>
                  <div className="score-value">{score}</div>
                  <div className="score-bar-container">
                    <div className="score-bar-fill" style={{ width: `${parseFloat(score) || 0}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="section-header">
              <div className="pill">Performance signals</div>
              <div className="muted small">Projected readiness</div>
            </div>
            <div className="performance-grid tight">
              <div className="performance-item">
                <div className="performance-label">Job Performance</div>
                <div className="performance-value">{performance.JobPerformance}%</div>
              </div>
              <div className="performance-item">
                <div className="performance-label">Academic Performance</div>
                <div className="performance-value">{performance.AcademicPerformance}%</div>
              </div>
            </div>
          </div>

          {result?.analysis && (
            <div className="card wide">
              <div className="section-header">
                <div className="pill">AI narrative</div>
                <div className="muted small">Tailored summary</div>
              </div>
              <div className="analysis-content" dangerouslySetInnerHTML={{ __html: result.analysis || '' }} />
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default Results;
