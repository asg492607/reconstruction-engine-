import React, { useState, useEffect } from 'react';
import { 
  Menu, 
  ShieldCheck, 
  Play, 
  Loader2, 
  Clock, 
  Plus, 
  FileCheck2,
  Lock,
  ChevronRight,
  ShieldAlert,
  Terminal,
  Activity
} from 'lucide-react';

export default function TopHeader({
  onOpenMobileMenu,
  activeCase,
  activeTab,
  onTriggerReconstruction,
  reconstructionLoading,
  onNavigate,
  onNewCase
}) {
  const [istTime, setIstTime] = useState('');
  const utcTime = istTime; // Backward-compatible fallback for any cached HMR bundle

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      try {
        const parts = new Intl.DateTimeFormat('en-GB', {
          timeZone: 'Asia/Kolkata',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        }).formatToParts(now);

        const map = {};
        parts.forEach(p => { map[p.type] = p.value; });
        setIstTime(`${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second} IST`);
      } catch (e) {
        const istOffset = 5.5 * 60 * 60 * 1000;
        const istDate = new Date(now.getTime() + istOffset);
        setIstTime(istDate.toISOString().replace('T', ' ').substring(0, 19) + ' IST');
      }
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getTabTitle = (tab) => {
    switch(tab) {
      case 'overview': return 'Command HUD';
      case 'board': return 'Detective Case Canvas';
      case 'plan': return 'Dynamic Analysis Plan';
      case 'evidence': return 'Evidence Vault';
      case 'ocr': return 'Forensic OCR Terminal';
      case 'timeline': return 'Synchronized Timeline';
      case 'reconstruction': return 'Reconstruction Studio';
      case 'gaps': return 'Gaps & Conflicts Radar';
      case 'entities': return 'Candidate Entities';
      case 'copilot': return 'AI Copilot Assistant';
      case 'output':
      case 'dossier': return 'Investigation Dossier';
      default: return 'Investigation Console';
    }
  };

  return (
    <header className="top-content-header">
      {/* Left side: Mobile Menu Trigger + Breadcrumb */}
      <div className="header-left-zone">
        <button
          type="button"
          onClick={onOpenMobileMenu}
          className="header-mobile-menu-btn"
          aria-label="Open navigation sidebar"
          title="Open Menu"
        >
          <Menu size={20} strokeWidth={2.4} />
        </button>

        <div className="header-breadcrumb">
          <span className="crumb-root">RRE 2.0</span>
          <ChevronRight size={13} className="crumb-sep" />
          <span className="crumb-case">
            {activeCase?.case_number || 'SEC-2026-SHOWCASE'}
          </span>
          <ChevronRight size={13} className="crumb-sep" />
          <span className="crumb-active">
            {getTabTitle(activeTab)}
          </span>
        </div>
      </div>

      {/* Right side: Telemetry + Quick Actions */}
      <div className="header-right-zone">
        {/* Live IST Clock */}
        <div className="header-clock-chip" title="Indian Standard Time (IST - UTC+05:30)">
          <Clock size={13} className="clock-icon" />
          <span className="clock-text">{istTime}</span>
        </div>

        {/* Chain of Custody Security Badge */}
        <div className="header-security-chip" title="SHA-256 Cryptographic Immutability Enforced">
          <Lock size={12} />
          <span>SHA-256 VAULT SECURED</span>
        </div>

        {/* Case Status Pill */}
        <div className="header-status-chip">
          <span className="pulse-dot-green" />
          <span>{activeCase?.status || 'RECONSTRUCTION'}</span>
        </div>

        {/* Action: Trigger Reconstruction */}
        {onTriggerReconstruction && activeCase && (
          <button
            onClick={onTriggerReconstruction}
            disabled={reconstructionLoading}
            className="header-action-btn primary"
            title="Execute Dynamic Reconstruction Pipeline"
          >
            {reconstructionLoading ? (
              <>
                <Loader2 size={13} className="spin" />
                <span className="btn-text">RECONSTRUCTING...</span>
              </>
            ) : (
              <>
                <Play size={13} fill="currentColor" />
                <span className="btn-text">RUN RECONSTRUCTION</span>
              </>
            )}
          </button>
        )}

        {/* Action: View Dossier Report */}
        {onNavigate && activeTab !== 'output' && (
          <button
            onClick={() => onNavigate('output')}
            className="header-action-btn secondary"
            title="View Official Dossier Report"
          >
            <FileCheck2 size={13} />
            <span className="btn-text">VIEW DOSSIER</span>
          </button>
        )}
      </div>
    </header>
  );
}
