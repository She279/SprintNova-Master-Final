export function AuthShell({ eyebrow, title, subtitle, children }) {
  return <div className="auth-page">
    <section className="auth-visual">
      <div className="auth-glow glow-one"/><div className="auth-glow glow-two"/>
      <div className="auth-brand"><div className="brand-mark">S</div><span>SprintNova</span></div>
      <div className="auth-hero">
        <span className="auth-kicker">AI-powered agile delivery</span>
        <h2>Turn every sprint into <em>visible progress.</em></h2>
        <p>One workspace for projects, people, quality, delivery and intelligent risk signals.</p>
        <div className="auth-flow"><span>Plan</span><i/> <span>Build</span><i/> <span>Test</span><i/> <span>Deliver</span></div>
      </div>
      <div className="auth-stat-row"><div><strong>01</strong><span>Plan with clarity</span></div><div><strong>02</strong><span>Work with context</span></div><div><strong>03</strong><span>Deliver with confidence</span></div></div>
    </section>
    <section className="auth-form-side"><div className="auth-form-wrap">
      {eyebrow && <p className="auth-eyebrow">{eyebrow}</p>}<h1>{title}</h1>{subtitle && <p className="auth-subtitle">{subtitle}</p>}<div className="auth-form">{children}</div>
      <p className="auth-footer">SprintNova · Secure company workspace</p>
    </div></section>
  </div>;
}
