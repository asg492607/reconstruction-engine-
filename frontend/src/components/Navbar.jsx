import React, { useState } from 'react';
import { 
  Shield, 
  Layers, 
  FileText, 
  AlertTriangle, 
  GitBranch, 
  Cpu, 
  Users, 
  LogOut, 
  Menu, 
  X,
  Briefcase,
  ChevronDown,
  Database
} from 'lucide-react';

export default function Navbar({ 
  user, 
  onLogout, 
  activeTab, 
  setActiveTab, 
  cases = [], 
  activeCase, 
  onSelectCase 
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: Layers },
    { id: 'evidence', label: 'Evidence Vault', icon: Database },
    { id: 'timeline', label: 'Timeline', icon: Layers },
    { id: 'reconstruction', label: 'Reconstruction', icon: GitBranch },
    { id: 'gaps', label: 'Gaps & Conflicts', icon: AlertTriangle },
    { id: 'entities', label: 'Entities', icon: Users },
    { id: 'copilot', label: 'AI Copilot', icon: Cpu },
    { id: 'dossier', label: 'Dossier', icon: FileText },
  ];

  const getRoleBadgeClass = (role) => {
    switch(role) {
      case 'LEAD_INVESTIGATOR': return 'badge-blue';
      case 'FORENSIC_SPECIALIST': return 'badge-purple';
      case 'FINANCIAL_AUDITOR': return 'badge-amber';
      case 'PROSECUTOR_JUDGE': return 'badge-green';
      default: return 'badge-slate';
    }
  };

  return (
    <header className="header-glass">
      <div className="container-xl" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '64px' }}>
        {/* Left: Brand & Case Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div 
            onClick={() => setActiveTab('overview')}
            style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
          >
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: 'var(--shadow-blue)'
            }}>
              <Shield size={20} />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--text-main)', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
                RRE <span style={{ color: 'var(--primary)', fontWeight: 600 }}>2.0</span>
              </div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                Reconstruction
              </div>
            </div>
          </div>

          {/* Case Dropdown */}
          {cases.length > 0 && (
            <div style={{ display: 'none', mdDisplay: 'flex', alignItems: 'center' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: 'var(--bg-subtle)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-light)',
                fontSize: '0.825rem'
              }}>
                <Briefcase size={14} color="var(--primary)" />
                <select
                  aria-label="Active Case Selection"
                  value={activeCase?.id || ''}
                  onChange={(e) => onSelectCase(e.target.value)}
                  style={{
                    border: 'none',
                    background: 'transparent',
                    fontWeight: 600,
                    color: 'var(--text-main)',
                    cursor: 'pointer',
                    outline: 'none',
                    maxWidth: '220px'
                  }}
                >
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.case_number}: {c.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Center: Desktop Nav Tabs */}
        <nav style={{ display: 'none', lgDisplay: 'flex', alignItems: 'center', gap: '4px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 11px',
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  fontSize: '0.825rem',
                  fontWeight: isActive ? 700 : 500,
                  backgroundColor: isActive ? 'var(--bg-accent-light)' : 'transparent',
                  color: isActive ? 'var(--primary)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={15} color={isActive ? 'var(--primary)' : 'currentColor'} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Right: User Profile & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ textAlign: 'right', display: 'none', smDisplay: 'block' }}>
                <div style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  {user.full_name || user.email?.split('@')[0]}
                </div>
                <div style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end', marginTop: '2px' }}>
                  <span className={`badge ${getRoleBadgeClass(user.role)}`}>
                    {user.role}
                  </span>
                </div>
              </div>

              <button
                onClick={onLogout}
                title="Sign Out"
                className="btn btn-secondary btn-sm"
                style={{ padding: '6px 10px' }}
              >
                <LogOut size={15} />
                <span style={{ display: 'none', smDisplay: 'inline' }}>Sign Out</span>
              </button>
            </div>
          )}

          {/* Mobile Hamburger Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{
              display: 'flex',
              lgDisplay: 'none',
              padding: '8px',
              background: 'none',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-main)',
              cursor: 'pointer'
            }}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div style={{
          backgroundColor: '#ffffff',
          borderBottom: '1px solid var(--border-light)',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {cases.length > 0 && (
            <div style={{ marginBottom: '8px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Active Case
              </label>
              <select
                aria-label="Mobile Active Case Selection"
                value={activeCase?.id || ''}
                onChange={(e) => {
                  onSelectCase(e.target.value);
                  setMobileMenuOpen(false);
                }}
                className="form-select"
              >
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.case_number}: {c.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginTop: '4px' }}>
            Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setMobileMenuOpen(false);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  fontSize: '0.9rem',
                  fontWeight: isActive ? 700 : 500,
                  backgroundColor: isActive ? 'var(--bg-accent-light)' : 'transparent',
                  color: isActive ? 'var(--primary)' : 'var(--text-main)',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                <Icon size={18} color={isActive ? 'var(--primary)' : 'currentColor'} />
                {item.label}
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
}
