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
          <h1>AI-Powered Personality Assessment & Performance Prediction</h1>
          <p className="lede">
            Measure Big Five personality traits, predict academic and job performance, and store results in a semantic knowledge base for future analysis.
          </p>
          <div className="actions">
            <a className="btn primary" href="/assessment">Start Personality Assessment</a>
            <a className="btn ghost" href="#why">Learn More</a>
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
          <h2>Ontology & Data Model</h2>
          <p className="muted">
            Unlike traditional systems, our platform stores all assessment data in an RDF/OWL ontology, enabling semantic reasoning, querying, and future AI integration.
          </p>
          
          <div className="grid stats">
            <div className="card">
              <div className="pill">Highlight Feature</div>
              <h3>Core Data Entities</h3>
              <div className="tags" style={{marginTop: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
                <span className="tag">Participant</span>
                <span className="tag">Assessment</span>
                <span className="tag">PersonalityTrait</span>
                <span className="tag">TraitScore</span>
                <span className="tag">PerformancePrediction</span>
              </div>
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

        <section className="panel" id="privacy">
          <h2>Privacy & Ethics</h2>
          <p className="muted">Your trust is our priority. We handle personality data with the highest standards of security and ethics.</p>
          <div className="grid feature-row" style={{ marginTop: '2rem' }}>
            <div className="card">
              <h3>Secure Storage</h3>
              <p className="muted small">Data stored securely.</p>
            </div>
            <div className="card">
              <h3>Consent First</h3>
              <p className="muted small">No public sharing without consent.</p>
            </div>
            <div className="card">
              <h3>Research Focused</h3>
              <p className="muted small">Semantic data used for research & analysis only.</p>
            </div>
          </div>
        </section>

        <section className="panel" id="about">
          <h2>About the Project</h2>
          <p className="muted">
            This project was developed as part of the <strong>Knowledge Representation and Reasoning (KRR)</strong> course. 
            It demonstrates the application of semantic web technologies in personality assessment and performance prediction.
          </p>

          <h3 style={{marginTop: '2rem', marginBottom: '1rem'}}>Meet the Team</h3>
          <div className="grid feature-row">
            <div className="card" style={{textAlign: 'center'}}>
              <div style={{width: '80px', height: '80px', background: 'rgba(255,255,255,0.1)', borderRadius: '50%', margin: '0 auto 1rem', display: 'grid', placeItems: 'center'}}>
                <span style={{fontSize: '24px'}}>👤</span>
              </div>
              <h3>Teammate 1</h3>
              <p className="muted small">Team Member</p>
            </div>
            <div className="card" style={{textAlign: 'center'}}>
              <div style={{width: '80px', height: '80px', background: 'rgba(255,255,255,0.1)', borderRadius: '50%', margin: '0 auto 1rem', display: 'grid', placeItems: 'center'}}>
                <span style={{fontSize: '24px'}}>👤</span>
              </div>
              <h3>Teammate 2</h3>
              <p className="muted small">Team Member</p>
            </div>
            <div className="card" style={{textAlign: 'center'}}>
              <div style={{width: '80px', height: '80px', background: 'rgba(255,255,255,0.1)', borderRadius: '50%', margin: '0 auto 1rem', display: 'grid', placeItems: 'center'}}>
                <span style={{fontSize: '24px'}}>👤</span>
              </div>
              <h3>Teammate 3</h3>
              <p className="muted small">Team Member</p>
            </div>
            <div className="card" style={{textAlign: 'center', borderColor: 'var(--accent)'}}>
               <div style={{width: '80px', height: '80px', background: 'linear-gradient(135deg, var(--accent), var(--accent-2))', borderRadius: '50%', margin: '0 auto 1rem', display: 'grid', placeItems: 'center'}}>
                <span style={{fontSize: '24px', color: '#000'}}>🎓</span>
              </div>
              <h3>Supervisor Name</h3>
              <p className="muted small" style={{color: 'var(--accent)'}}>Project Supervisor</p>
            </div>
          </div>
        </section>

        <section className="panel cta" id="cta">
          <h2>Ready to discover your personality profile and performance potential?</h2>
          <div className="actions">
            <a className="btn primary" href="/assessment">Start Assessment</a>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Landing;
