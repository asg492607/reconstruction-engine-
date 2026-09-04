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
              style={{ display: 'none', mdDisplay: 'inline-flex' }}
            >
              <Sparkles size={16} color="var(--primary)" />
              Try Live Demo
            </button>
            <button 
              onClick={onOpenAuth}
              className="btn btn-primary"
            >
              Sign In / Register
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
        <div style={{ maxWidth: '880px', margin: '0 auto' }}>
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
            Theft Investigation & Multi-Modal Reconstruction Platform
          </div>

          <h1 style={{
            fontSize: 'clamp(2.2rem, 5vw, 3.75rem)',
            fontWeight: 800,
            color: 'var(--text-main)',
            lineHeight: 1.15,
            letterSpacing: '-0.03em',
            marginBottom: '20px'
          }}>
            Reconstruct Crime Reality with <span style={{ color: 'var(--primary)' }}>Empirical Precision</span>
          </h1>

          <p style={{
            fontSize: 'clamp(1rem, 2vw, 1.25rem)',
            color: 'var(--text-muted)',
            lineHeight: 1.6,
            marginBottom: '36px',
            maxWidth: '720px',
            marginLeft: 'auto',
            marginRight: 'auto'
          }}>
            Synthesize physical toolmarks, CCTV sequences, cyber audit trails, and financial records into validated timelines. Self-challenging AI models present provable hypotheses while preserving evidentiary integrity.
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
              Launch Platform
              <ArrowRight size={18} />
            </button>
            <button 
              onClick={() => onQuickDemo('LEAD')}
              className="btn btn-outline"
              style={{ padding: '12px 24px', fontSize: '1rem' }}
            >
              <Database size={18} />
              Open Case THF-2026-0001
            </button>
          </div>

          {/* Trust Safeguards Bar */}
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
              SHA-256 Tamper Evident
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={16} color="var(--primary)" />
              Strict ABAC Departmental Routing
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={16} color="var(--primary)" />
              Judicial Non-Automated Guilt Guarantee
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={16} color="var(--primary)" />
              Live Gemini 3.6 Flash Engine
            </div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section style={{ padding: '70px 16px', backgroundColor: '#f8fafc' }}>
        <div className="container-xl">
          <div style={{ textAlign: 'center', marginBottom: '48px' }}>
            <h2 style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '12px' }}>
              Built for Specialized Investigation Disciplines
            </h2>
            <p style={{ color: 'var(--text-muted)', maxWidth: '640px', margin: '0 auto', fontSize: '0.95rem' }}>
              Departmental separation ensures evidence stays segregated by domain while synthesizing into high-fidelity reconstruction hypotheses.
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
                Multi-Source Intake & Routing
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                Automatically classifies physical forensics, CCTV videos, audit logs, witness statements, and invoices into appropriate departmental queues.
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
                Correlated Master Timeline
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                Synthesizes disparate evidence timestamps onto a normalized timeline. Highlights temporal clusters and automatically flags coverage blackouts.
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
                Cross-references testimony against empirical telemetry (e.g., CCTV timestamps vs witness claims) to surface contradictions and investigation gaps.
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
                Self-Challenging Hypotheses
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                Generates competing theft hypotheses (e.g., forced entry vs inside collusion), submits them to automated counter-argument tests, and leaves human investigators in control.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Role Demonstration Showcase */}
      <section style={{ padding: '60px 16px', backgroundColor: '#ffffff' }}>
        <div className="container-xl" style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.65rem', fontWeight: 800, marginBottom: '10px' }}>
            Tailored Role Dashboards
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '32px' }}>
            Click below to inspect the platform through specific role perspectives:
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
              🕵️ Lead Investigator
            </button>
            <button 
              onClick={() => onQuickDemo('FORENSIC')}
              className="btn btn-outline"
            >
              🔬 Forensic Specialist
            </button>
            <button 
              onClick={() => onQuickDemo('FINANCIAL')}
              className="btn btn-outline"
            >
              💼 Financial Auditor
            </button>
            <button 
              onClick={() => onQuickDemo('JUDGE')}
              className="btn btn-outline"
            >
              ⚖️ Prosecutor / Magistrate
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
            Reality Reconstruction Engine (RRE) • Law Enforcement AI Framework
          </div>
          <div>
            Adheres to ISO/IEC 27037 Digital Forensics Standards • Model Transparency & Evidentiary Safeguards Guaranteed
          </div>
        </div>
      </footer>
    </div>
  );
}
