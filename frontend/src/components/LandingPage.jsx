import React from 'react';
import { 
  Shield, 
  Search, 
  FileText, 
  Cpu, 
  Lock, 
  CheckCircle, 
  AlertTriangle, 
  Database, 
  ArrowRight, 
  Eye, 
  Sparkles,
  Layers,
  Scale
} from 'lucide-react';

export default function LandingPage({ onOpenAuth, onQuickDemo }) {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#ffffff' }}>
      {/* Top Navbar */}
      <header style={{
        borderBottom: '1px solid var(--border-light)',
        backgroundColor: '#ffffff',
        position: 'sticky',
        top: 0,
        zIndex: 40
      }}>
        <div className="container-xl" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '70px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              backgroundColor: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: 'var(--shadow-blue)'
            }}>
              <Shield size={22} />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
                RRE <span style={{ color: 'var(--primary)', fontWeight: 600 }}>2.0</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                Reality Reconstruction Engine
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button 
              onClick={() => onQuickDemo('LEAD')}
              className="btn btn-secondary"
            >
              <Sparkles size={16} color="var(--primary)" />
              Try Live Demo
            </button>
            <button 
              onClick={onOpenAuth}
              className="btn btn-primary"
            >
              Sign In / Access
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section style={{
        background: 'linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)',
        padding: '80px 16px 60px 16px',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '920px', margin: '0 auto' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--primary-border)',
            padding: '6px 14px',
            borderRadius: '999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            color: 'var(--primary)',
            boxShadow: 'var(--shadow-sm)',
            marginBottom: '24px'
          }}>
            <Sparkles size={14} />
            Evidence Intelligence & Reconstruction Platform
          </div>

          <h1 style={{
            fontSize: 'clamp(2.2rem, 5vw, 3.6rem)',
            fontWeight: 800,
            color: 'var(--text-main)',
            lineHeight: 1.18,
            letterSpacing: '-0.03em',
            marginBottom: '20px'
          }}>
            Synthesize Heterogeneous Theft Evidence into <span style={{ color: 'var(--primary)' }}>Traceable Intelligence</span>
          </h1>

          <p style={{
            fontSize: 'clamp(1rem, 2vw, 1.2rem)',
            color: 'var(--text-muted)',
            lineHeight: 1.6,
            marginBottom: '36px',
            maxWidth: '780px',
            marginLeft: 'auto',
            marginRight: 'auto'
          }}>
            RRE transforms scattered theft evidence into traceable observations, routes evidence to authorized specialist departments, correlates independent findings across time and entities, and generates evidence-constrained hypotheses for investigator review.
          </p>

          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: '14px',
            marginBottom: '48px'
          }}>
            <button 
              onClick={onOpenAuth}
              className="btn btn-primary"
              style={{ padding: '12px 28px', fontSize: '1rem' }}
            >
              Open Workstation
              <ArrowRight size={18} />
            </button>
            <button 
              onClick={() => onQuickDemo('LEAD')}
              className="btn btn-outline"
              style={{ padding: '12px 24px', fontSize: '1rem' }}
            >
              <Database size={18} />
              Explore Demo Case (Electronics Store Burglary)
            </button>
          </div>

          {/* Core Design Principles Bar */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '24px',
            color: 'var(--text-muted)',
            fontSize: '0.825rem',
            fontWeight: 500
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={16} color="var(--primary)" />
              SHA-256 Tamper-Evident Hashing
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={16} color="var(--primary)" />
              Two-Layer Deterministic & AI Challenge
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={16} color="var(--primary)" />
              Non-Verdict Design: Human Decisions in Control
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={16} color="var(--primary)" />
              Digital Evidence Preservation Informed
            </div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section style={{ padding: '70px 16px', backgroundColor: '#f8fafc' }}>
        <div className="container-xl">
          <div style={{ textAlign: 'center', marginBottom: '48px' }}>
            <h2 style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '12px' }}>
              Specialized Departmental Analysis & Correlation
            </h2>
            <p style={{ color: 'var(--text-muted)', maxWidth: '680px', margin: '0 auto', fontSize: '0.95rem' }}>
              Departments analyze evidence independently within their authorized queues, while the correlation layer synthesizes unified timelines and highlights cross-source inconsistencies.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px'
          }}>
            {/* Card 1 */}
            <div className="card" style={{ padding: '24px' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                backgroundColor: 'var(--info-bg)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <Search size={24} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px' }}>
                Classification & Departmental Policy Routing
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                Classifies incoming files into evidence types and evaluates analysis recommendations against strict Attribute-Based Access Control (ABAC) policies.
              </p>
            </div>

            {/* Card 2 */}
            <div className="card" style={{ padding: '24px' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                backgroundColor: 'var(--purple-bg)',
                color: 'var(--purple-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <Layers size={24} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px' }}>
                Multi-Source Chronology & Provenance
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                Normalizes camera clocks, access logs, and inventory audit timestamps onto a correlated timeline with full data provenance back to original files.
              </p>
            </div>

            {/* Card 3 */}
            <div className="card" style={{ padding: '24px' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                backgroundColor: 'var(--warning-bg)',
                color: 'var(--warning-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <AlertTriangle size={24} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px' }}>
                Gaps & Conflicts Radar
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                Flags surveillance coverage voids and highlights contradictions between witness statements and electronic telemetry for human investigator resolution.
              </p>
            </div>

            {/* Card 4 */}
            <div className="card" style={{ padding: '24px' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                backgroundColor: 'var(--success-bg)',
                color: 'var(--success-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <Scale size={24} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px' }}>
                Evidence Support Levels & Self-Challenge
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                Synthesizes competing theft explanations, evaluates support levels (Strong / Moderate / Speculative), and subjects each hypothesis to deterministic and AI counter-point tests.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Role Demonstration Showcase */}
      <section style={{ padding: '60px 16px', backgroundColor: '#ffffff' }}>
        <div className="container-xl" style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.65rem', fontWeight: 800, marginBottom: '10px' }}>
            Workstation Views by Operational Role
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '32px' }}>
            Select an operational perspective to inspect how RRE organizes and presents specialized findings:
          </p>

          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: '12px'
          }}>
            <button 
              onClick={() => onQuickDemo('LEAD')}
              className="btn btn-outline"
            >
              🕵️ Lead Investigator Workstation
            </button>
            <button 
              onClick={() => onQuickDemo('FORENSIC')}
              className="btn btn-outline"
            >
              🔬 Forensic Specialist Workstation
            </button>
            <button 
              onClick={() => onQuickDemo('FINANCIAL')}
              className="btn btn-outline"
            >
              💼 Financial Crimes & Loss Analyst
            </button>
            <button 
              onClick={() => onQuickDemo('JUDGE')}
              className="btn btn-outline"
            >
              📋 External Legal Review & Report Export
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-light)',
        padding: '36px 16px',
        backgroundColor: '#ffffff',
        textAlign: 'center',
        fontSize: '0.825rem',
        color: 'var(--text-muted)'
      }}>
        <div className="container-xl">
          <div style={{ fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
            Reality Reconstruction Engine (RRE 2.0) • Evidence Intelligence Platform
          </div>
          <div>
            Built on Non-Verdict Design Principles • Evidence handling informed by digital preservation standards • Human investigators maintain exclusive decision authority
          </div>
        </div>
      </footer>
    </div>
  );
}
