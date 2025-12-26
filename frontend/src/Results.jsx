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

  // Simple Markdown Parser for the specific format returned by the AI
  const renderAnalysis = (text) => {
    if (!text) return null;

    // Split by headers (###)
    const sections = text.split('###').filter(s => s.trim());

    return sections.map((section, index) => {
      const lines = section.trim().split('\n');
      const title = lines[0].trim();
      // Filter out empty lines
      const contentLines = lines.slice(1).filter(l => l.trim());

      // Check if content looks like a list (starts with *, -, or number)
      const isList = contentLines.some(l => /^[*-]|\d+\./.test(l.trim()));
      
      let renderedContent;
      if (isList) {
        renderedContent = (
          <div className="analysis-list-grid">
            {contentLines.map((line, i) => {
              // Remove list markers (*, -, 1.)
              let cleanLine = line.trim().replace(/^([*-]|\d+\.)\s*/, '');
              
              // Check for bold text **Title**
              const parts = cleanLine.split('**');
              
              // If we have bold text, we assume it's a header-description pair
              // Format: **Header:** Description
              if (parts.length >= 3) {
                const header = parts[1];
                const description = parts.slice(2).join('**').replace(/^[:\s]+/, ''); // Remove leading colon/space
                
                return (
                  <div key={i} className="analysis-card-item">
                    <div className="analysis-item-icon">✦</div>
                    <div className="analysis-item-content">
                      <div className="analysis-item-title">{header}</div>
                      <div className="analysis-item-desc">{description || parts[0]}</div> 
                    </div>
                  </div>
                );
              }
              
              // Fallback for items without bold formatting or just plain text
              return (
                <div key={i} className="analysis-card-item simple">
                   <div className="analysis-item-icon">✦</div>
                   <div className="analysis-item-content">
                     <div className="analysis-item-desc">{cleanLine}</div>
                   </div>
                </div>
              );
            })}
          </div>
        );
      } else {
        // Paragraph text
        renderedContent = (
          <div className="analysis-text-block">
            {contentLines.map((line, i) => (
              <p key={i} className="analysis-text">{line}</p>
            ))}
          </div>
        );
      }

      return (
        <div className="analysis-block" key={index}>
          <h3 className="analysis-title">{title}</h3>
          {renderedContent}
        </div>
      );
    });
  };

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

          <div className="card wide">
            <div className="section-header">
              <div className="pill">Performance signals</div>
              <div className="muted small">Projected readiness</div>
            </div>
            <div className="performance-grid">
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
            <div className="card wide analysis-card-container">
              <div className="section-header">
                <div className="pill">AI narrative</div>
                <div className="muted small">Tailored summary</div>
              </div>
              <div className="analysis-content-wrapper">
                {renderAnalysis(result.analysis)}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default Results;
