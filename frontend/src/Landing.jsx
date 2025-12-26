import React, { useState } from 'react';

// Import local photos if they exist. 
// Note: In Vite, if these files don't exist at build time, it might throw an error.
// A safer way for optional assets is to use the public folder or try/catch in require (not available in ESM).
// Here we will use a helper to try to load them, or fallback to the UI Avatar URL.

// Helper to get image URL with fallback
const getAvatar = (name, filename, isSupervisor = false) => {
  // We try to construct a URL for the public folder or src assets.
  // Since we can't easily check file existence in the browser without a request,
  // we will return the local path and let the <img> onError handler switch to the fallback.
  
  // Assuming user puts images in src/assets/photos/filename
  // But dynamic imports of non-existent files break builds.
  // So we will use the URL constructor for a known path pattern if using Vite's asset handling,
  // OR simply point to the file and handle error.
  
  // For this solution, we will return an object with { src, fallback }
  const fallbackBg = isSupervisor ? 'fbbf24' : 'random';
  const fallbackColor = isSupervisor ? '000' : 'fff';
  const fallbackUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=${fallbackBg}&color=${fallbackColor}&size=128`;

  // We'll try to use the imported images if we could, but since we can't guarantee they exist,
  // we will use a pattern that assumes they might be there.
  // However, to avoid build errors, we can't import missing files.
  
  // BEST APPROACH: Use the `onError` event in the JSX.
  // We will point `src` to the local file (assuming it's imported or in public).
  // Since the user created `src/assets/photos`, we really should import them.
  // But we can't import what doesn't exist.
  
  // So we will return the fallback as the default, and the user can uncomment imports later?
  // No, the user asked for "if image is not present it show the default".
  
  return fallbackUrl; 
};

const TeamMember = ({ name, role, filename, isSupervisor = false }) => {
  // We use a state to manage the image source. 
  // We try to load the local image first (using a dynamic import pattern that Vite supports for assets).
  // If that fails (or file doesn't exist), we fall back to the avatar.
  
  // However, dynamic import(`...`) is async. 
  // A simpler way for "src/assets" is to use the glob import feature of Vite.
  
  const [imgSrc, setImgSrc] = useState(null);

  // We can try to find the image in the glob of all photos
  // This is safe because it only includes files that actually exist.
  const photos = import.meta.glob('./assets/photos/*.{png,jpg,jpeg,svg}', { eager: true });
  
  // Try to find a matching file
  const foundPath = Object.keys(photos).find(path => path.includes(filename));
  const localImage = foundPath ? photos[foundPath].default : null;

  const fallbackBg = isSupervisor ? 'fbbf24' : 'random';
  const fallbackColor = isSupervisor ? '000' : 'fff';
  const fallbackUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=${fallbackBg}&color=${fallbackColor}&size=128`;

  return (
    <div className={`team-card ${isSupervisor ? 'supervisor' : ''}`}>
      <img 
        src={localImage || fallbackUrl} 
        alt={name} 
        className="team-avatar-img"
        onError={(e) => { e.target.onerror = null; e.target.src = fallbackUrl; }}
      />
      <h3 className="team-name">{name}</h3>
      <p className="team-role">{role}</p>
    </div>
  );
};

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
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="page">
      <header className="nav">
        <div className="nav-left">
          <div className="badge">PI</div>
          <span className="brand">Persona Insights</span>
        </div>
        
        <button 
          className="mobile-menu-btn" 
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Toggle menu"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {isMenuOpen ? (
              <path d="M18 6L6 18M6 6l12 12" />
            ) : (
              <path d="M3 12h18M3 6h18M3 18h18" />
            )}
          </svg>
        </button>

        <div className={`nav-actions ${isMenuOpen ? 'open' : ''}`}>
          <a href="#why" className="link" onClick={() => setIsMenuOpen(false)}>Why it matters</a>
          <a href="#how" className="link" onClick={() => setIsMenuOpen(false)}>How it works</a>
          <a href="#ontology" className="link" onClick={() => setIsMenuOpen(false)}>Ontology</a>
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
          <div className="team-grid">
            <TeamMember name="Talha Rusman" role="Team Member" filename="talha" />
            <TeamMember name="Raghib Rizwan" role="Team Member" filename="raghib" />
            <TeamMember name="Muhammad Umar" role="Team Member" filename="umar" />
            <TeamMember name="Muhammad Rafi" role="Project Supervisor" filename="rafi" isSupervisor={true} />
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
