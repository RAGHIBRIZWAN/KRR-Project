import React, { useEffect, useState } from 'react';

const API_BASE = window.location.port === '5173' ? 'http://localhost:5000' : '';

const Results = () => {
  const [payload, setPayload] = useState(null);
  const [selectedSection, setSelectedSection] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [justificationText, setJustificationText] = useState('');
  const [justificationLoading, setJustificationLoading] = useState(false);
  const [justificationError, setJustificationError] = useState('');
  const [careerFit, setCareerFit] = useState(null);
  const [careerFitLoading, setCareerFitLoading] = useState(false);
  const [careerFitError, setCareerFitError] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);

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

  useEffect(() => {
    const fetchJustification = async () => {
      if (!payload?.userId) return;
      setJustificationLoading(true);
      setJustificationError('');
      try {
        const res = await fetch(`${API_BASE}/api/justification/${encodeURIComponent(payload.userId)}`);
        const data = await res.json();
        if (!data?.found) {
          setJustificationError(data?.message || 'No justification found.');
          setJustificationText('');
        } else {
          setJustificationText(data.justification || '');
        }
      } catch (e) {
        setJustificationError('Could not load justification.');
      } finally {
        setJustificationLoading(false);
      }
    };

    fetchJustification();
  }, [payload?.userId]);

  useEffect(() => {
    const fetchCareerFit = async () => {
      if (!payload?.userId) return;
      setCareerFitLoading(true);
      setCareerFitError('');
      try {
        const res = await fetch(`${API_BASE}/api/career-fit/${encodeURIComponent(payload.userId)}`);
        const data = await res.json();
        if (!data?.found) {
          setCareerFitError(data?.message || 'Career role fit not available.');
          setCareerFit(null);
        } else {
          setCareerFit(data);
        }
      } catch (e) {
        setCareerFitError('Could not load career role fit.');
      } finally {
        setCareerFitLoading(false);
      }
    };

    fetchCareerFit();
  }, [payload?.userId]);

  useEffect(() => {
    const anyModalOpen = isModalOpen || isRoleModalOpen;
    if (!anyModalOpen) {
      document.body.style.overflow = '';
      return undefined;
    }

    const handler = (e) => {
      if (e.key === 'Escape') {
        setIsModalOpen(false);
        setIsRoleModalOpen(false);
      }
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handler);
    return () => {
      window.removeEventListener('keydown', handler);
      document.body.style.overflow = previousOverflow || '';
    };
  }, [isModalOpen, isRoleModalOpen]);

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

  const allSections = [
    'Trait-by-Trait Justification',
    'Agreeableness',
    'Conscientiousness',
    'Extraversion',
    'Neuroticism',
    'Openness',
    'Academic Performance Justification',
    'Academic Performance',
    'Job Performance Justification',
    'Job Performance',
    'Plain-English Summary'
  ];

  const isPerformanceSection = (section) => section?.toLowerCase().includes('performance');

  const escapeRegExp = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  const extractSectionContent = (text, sectionName) => {
    if (!text) return '';
    const lines = text.split(/\r?\n/);
    const isPerformance = isPerformanceSection(sectionName);

    const aliases = [sectionName];
    if (sectionName === 'Job Performance') aliases.unshift('Job Performance Justification');
    if (sectionName === 'Academic Performance') aliases.unshift('Academic Performance Justification');

    for (const name of aliases) {
      const startIndex = lines.findIndex((line) => line.toLowerCase().includes(name.toLowerCase()));
      if (startIndex !== -1) {
        const nextIndex = lines.slice(startIndex + 1).findIndex((line) => {
          return allSections.some((sec) => line.toLowerCase().includes(sec.toLowerCase()));
        });
        const endIndex = nextIndex === -1 ? lines.length : startIndex + 1 + nextIndex;
        const chunk = lines.slice(startIndex, endIndex).join('\n').trim();
        const contentLines = chunk.split(/\r?\n/).filter((l) => l.trim() !== '');
        if (contentLines.length >= (isPerformance ? 2 : 1)) return chunk;
      }
    }

    // Trait-specific keyword search inside the whole text
    const matched = lines.filter((line) => line.toLowerCase().includes(sectionName.toLowerCase()));
    if (matched.length >= (isPerformance ? 2 : 1)) return matched.join('\n').trim();

    // Fallback: only return full text for performance sections; otherwise empty to avoid bleed
    return isPerformance ? text.trim() : '';
  };

  const cleanSectionText = (raw, sectionName) => {
    if (!raw) return '';
    const lines = raw.split(/\r?\n/).filter((l) => l.trim() !== '');
    if (!lines.length) return raw;
    const normalizedSection = sectionName.toLowerCase();
    const isPerformance = isPerformanceSection(sectionName);

    // Strip the trait heading prefix from the first line while keeping its descriptive text
    const headingRegex = new RegExp(
      `^\\s*[-*\\d\\.\\)]*\\s*\\**${escapeRegExp(sectionName)}\\s*(?:\\([^)]*\\))?\\s*\\**\\s*:?\\s*`,
      'i'
    );

    const cleanedLines = lines.map((line, idx) => {
      if (idx > 0) return line; // Only the first line can carry the heading prefix
      const plain = line.toLowerCase();
      // Strip explicit "Justification" heading lines (e.g., "Justification**")
      if (/^\s*justification\**\s*:?\s*$/i.test(line)) return '';
      // Strip trait headings like "- **Agreeableness (58.0):**"
      if (plain.includes(normalizedSection)) {
        const strippedHeading = line.replace(headingRegex, '').trim();
        const strippedBullet = strippedHeading.replace(/^\s*([*-]|\d+\.)\s*/, '').trim();
        const cleaned = strippedBullet || strippedHeading;
        if (cleaned.length < 2) return '';
        return cleaned;
      }
      // If the line begins with a bullet, drop the marker
      const bulletStripped = line.replace(/^\s*([*-]|\d+\.)\s*/, '').trim();
      return bulletStripped || line;
    });

    // Remove any standalone justification headings from any position
    const cleanedWithoutHeadings = cleanedLines.filter((l) => !/^\s*justification\**\s*:?\s*$/i.test(l.trim()));

    let rebuilt = cleanedWithoutHeadings.join('\n').trim();
    // Final safeguard: drop a leading bullet/asterisk at start of content
    rebuilt = rebuilt.replace(/^\s*[*-]\s*/, '');
    const nonEmptyCount = rebuilt.split(/\r?\n/).filter((l) => l.trim() !== '').length;

    // Traits: accept any non-empty cleaned text, even single-line/short
    if (!isPerformance && rebuilt) return rebuilt;

    // Performance sections: allow short single-line cleaned content to show, as long as it's not empty
    if (isPerformance && rebuilt && nonEmptyCount >= 1) return rebuilt;

    // Fallback: only return raw for performance; traits fall back to cleaned (which may be empty)
    return isPerformance ? raw : rebuilt;
  };

  const handleCardClick = (section) => {
    setSelectedSection(section);
    setIsModalOpen(true);
  };

  const handleRoleCardClick = (role) => {
    setSelectedRole(role);
    setIsRoleModalOpen(true);
  };

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

  const roleEntries = careerFit?.roles
    ? Object.entries(careerFit.roles).map(([role, data]) => ({ role, score: data.score, position: null, data }))
    : [];

  const selectedRoleData = selectedRole && careerFit?.roles ? careerFit.roles[selectedRole] : null;

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
                <div
                  className="score-item clickable"
                  key={trait}
                  role="button"
                  tabIndex={0}
                  onClick={() => handleCardClick(trait)}
                  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleCardClick(trait)}
                >
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
              <div
                className="performance-item clickable"
                role="button"
                tabIndex={0}
                onClick={() => handleCardClick('Job Performance')}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleCardClick('Job Performance')}
              >
                <div className="performance-label">Job Performance</div>
                <div className="performance-value">{performance.JobPerformance}%</div>
              </div>
              <div
                className="performance-item clickable"
                role="button"
                tabIndex={0}
                onClick={() => handleCardClick('Academic Performance')}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleCardClick('Academic Performance')}
              >
                <div className="performance-label">Academic Performance</div>
                <div className="performance-value">{performance.AcademicPerformance}%</div>
              </div>
            </div>
          </div>

          <div className="card wide">
            <div className="section-header">
              <div className="pill">Career Role Fit</div>
              <div className="muted small">
                {careerFit?.top_recommendation ? `Top pick: ${careerFit.top_recommendation}` : 'Best-to-weakest fit ranking'}
              </div>
            </div>
            {careerFitLoading && <p className="muted">Crunching career role fit…</p>}
            {!careerFitLoading && careerFitError && <p className="muted">{careerFitError}</p>}
            {!careerFitLoading && !careerFitError && roleEntries.length > 0 && (
              <div className="career-grid">
                {roleEntries.map((entry) => {
                  const topTraits = (entry.data?.traits || []).slice(0, 2).map((t) => t.trait).join(', ');
                  const scoreVal = entry.score ?? entry.data?.score ?? 0;
                  const roleInitials = entry.role
                    .split(' ')
                    .map((w) => w[0])
                    .join('')
                    .slice(0, 2)
                    .toUpperCase();
                  return (
                    <div
                      className="career-card clickable"
                      key={entry.role}
                      role="button"
                      tabIndex={0}
                      onClick={() => handleRoleCardClick(entry.role)}
                      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleRoleCardClick(entry.role)}
                    >
                      <div className="career-card-top">
                        <div className="role-chip-stack">
                          <div className="role-icon">{roleInitials}</div>
                        </div>
                        <div className="career-score">{scoreVal}%</div>
                      </div>
                      <div className="career-card-mid">
                        <div className="career-role-name">{entry.role}</div>
                        <div className="muted small">Career match</div>
                      </div>
                      <div className="career-bar">
                        <div className="career-bar-fill" style={{ width: `${scoreVal}%` }} />
                      </div>
                      <div className="career-meta">
                        <span className="pill subtle">Fit indicator</span>
                        <span className="muted small">Top traits: {topTraits || 'Pending'}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            {!careerFitLoading && !careerFitError && roleEntries.length === 0 && (
              <p className="muted">Career fit will appear here after the assessment runs.</p>
            )}
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

      {isModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsModalOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{selectedSection}</h3>
              <button className="modal-close" onClick={() => setIsModalOpen(false)} aria-label="Close justification modal">
                ×
              </button>
            </div>
            <div className="modal-body">
              {justificationLoading && <p className="muted">Loading justification…</p>}
              {!justificationLoading && justificationError && <p className="muted">{justificationError}</p>}
              {!justificationLoading && !justificationError && (
                <pre className="justification-text">
                  {(() => {
                    const rawSection = extractSectionContent(justificationText, selectedSection);
                    const useFallback = isPerformanceSection(selectedSection);
                    const fallback = useFallback ? (justificationText || '') : '';
                    const cleaned = cleanSectionText(rawSection || fallback, selectedSection);
                    return cleaned || fallback || 'No justification available for this section.';
                  })()}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}

      {isRoleModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsRoleModalOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{selectedRole}</h3>
              <button className="modal-close" onClick={() => setIsRoleModalOpen(false)} aria-label="Close career role modal">
                ×
              </button>
            </div>
            <div className="modal-body">
              {selectedRoleData ? (
                <>
                  <div className="career-modal-header">
                    <div className="career-modal-score">
                      <div className="career-score-large">{selectedRoleData.score}%</div>
                      <div className="muted small">Fit score</div>
                    </div>
                    <div className="modal-badges">
                      <span className="pill subtle">{selectedRoleData.skill_gaps?.length ? 'Growth plan ready' : 'Strength-first'}</span>
                    </div>
                  </div>

                  {selectedRoleData.explanation && <p className="muted modal-explainer">{selectedRoleData.explanation}</p>}

                  <div className="modal-grid">
                    <div className="modal-tile">
                      <div className="modal-subtitle">Key trait drivers</div>
                      <div className="trait-chip-row">
                        {(selectedRoleData.traits || []).slice(0, 4).map((t) => (
                          <span className="trait-chip" key={t.trait}>
                            {t.trait}: {t.actual}% (target {t.target})
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="modal-tile">
                      <div className="modal-subtitle">Counterfactual insight</div>
                      <p className="muted small" style={{ lineHeight: 1.5 }}>{selectedRoleData.counterfactual || 'Maintain current balance to keep this fit strong.'}</p>
                    </div>
                  </div>

                  <div className="modal-grid two-col">
                    {selectedRoleData.strengths?.length > 0 && (
                      <div className="modal-tile">
                        <div className="modal-subtitle">Strengths</div>
                        <ul className="bullet-list tight">
                          {selectedRoleData.strengths.map((item, idx) => (
                            <li key={`${item}-${idx}`}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {selectedRoleData.challenges?.length > 0 && (
                      <div className="modal-tile">
                        <div className="modal-subtitle">Potential challenges</div>
                        <ul className="bullet-list tight">
                          {selectedRoleData.challenges.map((item, idx) => (
                            <li key={`${item}-${idx}`}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {selectedRoleData.skill_gaps?.length > 0 && (
                    <div className="career-modal-block">
                      <div className="modal-subtitle">Skill gap focus</div>
                      <div className="pill-row">
                        {selectedRoleData.skill_gaps.map((skill) => (
                          <span className="pill subtle" key={skill}>{skill}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="muted">No data available for this role.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Results;
