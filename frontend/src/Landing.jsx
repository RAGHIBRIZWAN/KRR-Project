import React from 'react';

const featureCards = [
  {
    title: 'Insights that read human',
    body: 'Groq-powered analysis turns raw scores into empathetic narratives—no spreadsheets required.'
  },
  {
    title: 'Job & academic outlook',
    body: 'Weighted models estimate on-the-job reliability and academic readiness from trait balance.'
  },
  {
    title: 'Data you can query',
    body: 'Results are stored as RDF/OWL entities so you can reason over cohorts, traits, and outcomes.'
  }
];

const howSteps = [
  'Questions load from the ontology. Every item is typed with traits and reverse-coding flags.',
  'Scores compute instantly. Reverse items flip, traits average, and percentages render for clarity.',
  'Performance signals derive. Weighted models project job and academic performance bands.',
  'AI crafts the story. A Groq prompt turns numbers into a concise, human-readable profile.',
  'Everything is saved semantically. Participants, assessments, and trait scores persist in RDF/OWL.'
];

const stats = [
  { label: 'Core traits mapped to every question', value: '5' },
  { label: 'Performance signals: job & academic', value: '2' },
  { label: 'Data stored with semantic structure', value: '100%' }
];

const Landing = () => {
  return (
    <div className="page">
      <header className="nav">
        <div className="nav-left">
          <div className="badge">PI</div>
          <span className="brand">Persona Insights</span>
        </div>
        <div className="nav-actions">
          <a href="#why" className="link">Why it matters</a>
          <a href="#how" className="link">How it works</a>
          <a href="#ontology" className="link">Ontology</a>
          <a href="#cta" className="link">Start</a>
        </div>
      </header>

      <main className="shell">
        <section className="panel hero" id="hero">
          <p className="eyebrow">Big Five, elevated</p>
          <h1>Understand the people behind your projects with science-backed personality insights.</h1>
          <p className="lede">
            Run a quick Big Five assessment, translate results into job and academic performance signals, and store everything in a semantic knowledge base you can actually query.
          </p>
          <div className="actions">
            <a className="btn primary" href="/assessment">Start the assessment</a>
            <a className="btn ghost" href="#why">See how it helps</a>
          </div>

          <div className="grid feature-row">
            {featureCards.map((card) => (
              <div className="card" key={card.title}>
                <div className="pill">Big Five</div>
                <h3>{card.title}</h3>
                <p className="muted small">{card.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="panel" id="why">
          <h2>Why this assessment</h2>
          <p className="muted">Fast signal on how people collaborate, learn, and deliver. Use it for hiring screens, team formation, or student coaching.</p>
          <div className="grid tags">
            <span className="tag">For teams</span>
            <span className="tag">For students</span>
            <span className="tag">For science</span>
          </div>
        </section>

        <section className="panel" id="how">
          <h2>How it works</h2>
          <ol className="steps">
            {howSteps.map((step, idx) => (
              <li key={step}>
                <span className="step-index">{idx + 1}</span>
                <div>{step}</div>
              </li>
            ))}
          </ol>
        </section>

        <section className="panel" id="ontology">
          <div className="grid stats">
            <div className="card">
              <div className="pill">Ontology-backed trust</div>
              <h3>Transparent, queryable data</h3>
              <p className="muted">Each assessment writes into the ontology with participants, trait scores, and predicted performance links. That means you can trace, audit, and reuse insights across systems—no black boxes.</p>
            </div>
            <div className="card stats-col">
              {stats.map((s) => (
                <div className="stat" key={s.label}>
                  <div className="stat-value">{s.value}</div>
                  <div className="muted small">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="panel cta" id="cta">
          <h2>Launch the assessment and see the narrative behind your numbers.</h2>
          <div className="actions">
            <a className="btn primary" href="/assessment">Start now</a>
            <a className="btn ghost" href="/results">View results</a>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Landing;
