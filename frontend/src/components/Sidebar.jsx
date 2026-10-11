import React, { useState } from 'react';
import { 
  Shield, 
  Layers, 
  AlertTriangle, 
  GitBranch, 
  Cpu, 
  Users, 
  LogOut, 
  Compass, 
  Database, 
  Clock, 
  Sparkles, 
  ShieldCheck, 
  Briefcase, 
  Plus, 
  ChevronLeft, 
  ChevronRight,
  X,
  Search,
  Fingerprint,
  Radio,
  FileCheck2
} from 'lucide-react';

export default function Sidebar({
  user,
  onLogout,
  activeTab,
  setActiveTab,
  cases = [],
  activeCase,
  onSelectCase,
  onNewCase,
  collapsed,
  setCollapsed,
  mobileOpen,
  setMobileOpen,
  evidenceCount = 0,
  eventsCount = 0,
  hypothesesCount = 0,
  gapsCount = 0
}) {
  const [filterQuery, setFilterQuery] = useState('');

  const navSections = [
    {
      title: 'COMMAND & CONTROL',
      items: [
        { id: 'overview', label: 'Command HUD', icon: Layers, tag: 'HUD' },
        { id: 'board', label: 'Detective Canvas', icon: Compass, tag: 'CANVAS' },
        { id: 'plan', label: 'Analysis DAG Plan', icon: Cpu, tag: 'DAG' },
      ]
    },
    {
      title: 'EVIDENTIARY VAULT',
      items: [
        { id: 'evidence', label: 'Evidence Vault', icon: Database, badge: evidenceCount },
        { id: 'ocr', label: 'Forensic OCR Terminal', icon: Fingerprint },
        { id: 'timeline', label: 'Correlated Timeline', icon: Clock, badge: eventsCount },
      ]
    },
    {
      title: 'RECONSTRUCTION MATRIX',
      items: [
        { id: 'reconstruction', label: 'Reconstruction Studio', icon: GitBranch, badge: hypothesesCount },
        { id: 'gaps', label: 'Gaps & Conflicts Radar', icon: AlertTriangle, badge: gapsCount, badgeVariant: 'warning' },
        { id: 'entities', label: 'Candidate Entities', icon: Users },
      ]
    },
    {
      title: 'INTELLIGENCE & EXPORT',
      items: [
        { id: 'copilot', label: 'AI Copilot Assistant', icon: Sparkles, tag: 'GEMINI' },
        { id: 'output', label: 'Judicial Dossier', icon: ShieldCheck, tag: 'VERIFIED' },
      ]
    }
  ];

  const getRoleBadgeStyle = (role) => {
    switch(role) {
      case 'LEAD_INVESTIGATOR': return { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' };
      case 'FORENSIC_OFFICER':
      case 'FORENSIC_SPECIALIST': return { bg: '#faf5ff', color: '#6d28d9', border: '#ddd6fe' };
      case 'FINANCIAL_ANALYST':
      case 'FINANCIAL_AUDITOR': return { bg: '#fffbeb', color: '#b45309', border: '#fde68a' };
      case 'LEGAL_REVIEWER':
      case 'PROSECUTOR_JUDGE': return { bg: '#ecfdf5', color: '#047857', border: '#a7f3d0' };
      case 'ADMIN': return { bg: '#fef2f2', color: '#b91c1c', border: '#fecaca' };
      default: return { bg: '#f1f5f9', color: '#334155', border: '#cbd5e1' };
    }
  };

  const roleStyle = getRoleBadgeStyle(user?.role);

  return (
    <>
      {/* Mobile Backdrop Overlay (strictly closes sidebar when clicked) */}
      {mobileOpen && (
        <div 
          onClick={() => setMobileOpen(false)}
          className="sidebar-backdrop"
          aria-hidden="true"
        />
      )}

      {/* Main Left Sidebar */}
      <aside 
        className={`app-sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}
        aria-label="Main Navigation"
      >
        {/* Top Header / Agency Brand */}
        <div className="sidebar-brand-wrapper">
          <div className="sidebar-brand" onClick={() => { setActiveTab('overview'); setMobileOpen(false); }}>
            <div className="brand-logo-box">
              <Shield size={20} strokeWidth={2.4} />
            </div>
            {!collapsed && (
              <div className="brand-text-block">
                <div className="brand-name">
                  RRE <span className="brand-version">2.0</span>
                </div>
                <div className="brand-subtitle">
                  EVIDENCE INTELLIGENCE
                </div>
              </div>
            )}
          </div>

          {/* Mobile Close Button */}
          <button 
            type="button"
            className="mobile-close-btn"
            onClick={() => setMobileOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        {/* System Telemetry Indicator & Agency Badge */}
        {!collapsed && (
          <div className="sidebar-telemetry">
            <div className="telemetry-pill">
              <span className="pulse-dot" />
              <span className="telemetry-text">FORENSIC ENGINE ACTIVE</span>
              <span className="telemetry-sub">METROPOLITAN POLICE</span>
            </div>
          </div>
        )}

        {/* Active Case Card in Sidebar */}
        {!collapsed && (
          <div className="sidebar-case-card">
            <div className="case-card-header">
              <div className="case-card-label-group">
                <Radio size={11} className="case-pulse-icon" />
                <span className="case-card-label">ACTIVE CASE</span>
              </div>
              {onNewCase && (
                <button 
                  onClick={() => { onNewCase(); setMobileOpen(false); }}
                  className="case-new-btn"
                  title="Register New Incident"
                >
                  <Plus size={11} strokeWidth={3} />
                  <span>NEW</span>
                </button>
              )}
            </div>

            {cases.length > 0 ? (
              <div className="case-select-wrapper">
                <Briefcase size={14} className="case-icon" />
                <select
                  value={activeCase?.id || ''}
                  onChange={(e) => {
                    onSelectCase(e.target.value);
                    setMobileOpen(false);
                  }}
                  className="case-select"
                  aria-label="Select Active Case"
                >
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.case_number}: {c.title}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="case-empty-msg">No active case loaded</div>
            )}

            {activeCase && (
              <div className="case-meta-row">
                <span className="case-meta-tag">{activeCase.case_type || 'THEFT'}</span>
                <span className="case-meta-tag">{activeCase.status || 'ACTIVE'}</span>
                <span className="case-meta-count">{evidenceCount} EXHIBITS</span>
              </div>
            )}
          </div>
        )}

        {/* Quick Filter Search Bar */}
        {!collapsed && (
          <div className="sidebar-search-box">
            <Search size={13} className="search-icon" />
            <input 
              type="text" 
              placeholder="Quick jump (e.g. Vault, Timeline)..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="sidebar-search-input"
            />
            {filterQuery && (
              <button 
                type="button" 
                onClick={() => setFilterQuery('')} 
                className="search-clear-btn"
              >
                ×
              </button>
            )}
          </div>
        )}

        {/* Navigation Items (Grouped by Category) */}
        <div className="sidebar-nav-scroll">
          {navSections.map((sec, secIdx) => {
            const visibleItems = sec.items.filter(item => 
              !filterQuery || item.label.toLowerCase().includes(filterQuery.toLowerCase())
            );

            if (visibleItems.length === 0) return null;

            return (
              <div key={secIdx} className="nav-group">
                {!collapsed && <div className="nav-group-title">{sec.title}</div>}

                <div className="nav-group-items">
                  {visibleItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id || (item.id === 'output' && activeTab === 'dossier');

                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          setActiveTab(item.id);
                          setMobileOpen(false);
                        }}
                        className={`nav-item-btn ${isActive ? 'active' : ''}`}
                        title={collapsed ? item.label : undefined}
                      >
                        <span className="nav-icon-box">
                          <Icon size={16} strokeWidth={isActive ? 2.4 : 1.9} />
                        </span>

                        {!collapsed && (
                          <span className="nav-label-text">
                            {item.label}
                          </span>
                        )}

                        {!collapsed && item.tag && (
                          <span className="nav-tag-chip">
                            {item.tag}
                          </span>
                        )}

                        {!collapsed && item.badge !== undefined && item.badge > 0 && (
                          <span className={`nav-badge ${item.badgeVariant === 'warning' ? 'badge-warn' : ''}`}>
                            {item.badge}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom Profile & Actions */}
        <div className="sidebar-footer">
          <div className="user-profile-card">
            <div className="user-avatar-circle" style={{ backgroundColor: roleStyle.bg, color: roleStyle.color, border: `1px solid ${roleStyle.border}` }}>
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>

            {!collapsed && (
              <div className="user-details-block">
                <div className="user-full-name">
                  {user?.full_name || user?.email?.split('@')[0]}
                </div>
                <div className="user-role-badge" style={{ backgroundColor: roleStyle.bg, color: roleStyle.color, borderColor: roleStyle.border }}>
                  {user?.role?.replace('_', ' ')}
                </div>
              </div>
            )}

            <button
              onClick={onLogout}
              className="logout-icon-btn"
              title="Sign Out of Session"
              aria-label="Sign Out"
            >
              <LogOut size={15} />
            </button>
          </div>

          {/* Desktop Sidebar Collapse Toggle */}
          <button 
            type="button"
            className="collapse-toggle-btn"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? "Expand navigation rail" : "Collapse navigation rail"}
            aria-label="Toggle sidebar collapse"
          >
            {collapsed ? <ChevronRight size={14} /> : (
              <>
                <ChevronLeft size={14} />
                <span>COLLAPSE RAIL</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
