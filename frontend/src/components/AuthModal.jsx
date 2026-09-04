import React, { useState } from 'react';
import { 
  X, 
  Lock, 
  Mail, 
  User, 
  Shield, 
  Briefcase, 
  Building, 
  Sparkles, 
  AlertCircle, 
  CheckCircle2,
  LogIn,
  UserPlus
} from 'lucide-react';
import { 
  auth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword 
} from '../firebase';
import { api } from '../api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [tab, setTab] = useState('login'); // 'login' | 'register' | 'demo'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('LEAD_INVESTIGATOR');
  const [department, setDepartment] = useState('INVESTIGATION');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleLogin = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // 1. First attempt Firebase Auth
      try {
        const userCred = await signInWithEmailAndPassword(auth, email, password);
        const idToken = await userCred.user.getIdToken();
        const syncResult = await api.auth.firebaseSync(idToken, role, department, fullName || userCred.user.displayName);
        onAuthSuccess(syncResult);
        onClose();
        return;
      } catch (fbErr) {
        console.warn("Firebase direct sign-in fallback to backend standard auth:", fbErr.message);
      }

      // 2. Fallback to direct backend auth (e.g. for pre-seeded test accounts)
      const data = await api.auth.login(email, password);
      onAuthSuccess(data);
      onClose();
    } catch (err) {
      setError(err.message || "Failed to sign in. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // 1. Create user in Firebase
      const userCred = await createUserWithEmailAndPassword(auth, email, password);
      const idToken = await userCred.user.getIdToken();

      // 2. Sync into backend database with selected Role & Department
      const syncResult = await api.auth.firebaseSync(idToken, role, department, fullName);
      onAuthSuccess(syncResult);
      onClose();
    } catch (err) {
      // If Firebase failed, fallback to direct backend registration
      try {
        await api.auth.register({
          email,
          password,
          full_name: fullName,
          role,
          department
        });
        const loginData = await api.auth.login(email, password);
        onAuthSuccess(loginData);
        onClose();
      } catch (backendErr) {
        setError(backendErr.message || err.message || "Registration failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (demoEmail, demoRole, demoDept) => {
    setEmail(demoEmail);
    setPassword('password123');
    setRole(demoRole);
    setDepartment(demoDept);
    setLoading(true);
    setError(null);

    try {
      const data = await api.auth.login(demoEmail, 'password123');
      onAuthSuccess(data);
      onClose();
    } catch (err) {
      setError(err.message || "Quick login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.45)',
      WebkitBackdropFilter: 'blur(4px)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '16px'
    }}>
      <div className="card animate-fade-in" style={{
        maxWidth: '480px',
        width: '100%',
        padding: '28px',
        position: 'relative',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        {/* Close Button */}
        <button 
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'none',
            border: 'none',
            color: 'var(--text-light)',
            cursor: 'pointer',
            padding: '4px'
          }}
        >
          <X size={20} />
        </button>

        {/* Modal Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            backgroundColor: 'var(--primary-light)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px auto'
          }}>
            <Shield size={24} />
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
            RRE Secure Access Portal
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            Firebase Authenticated & Role-Based Access Control
          </p>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          backgroundColor: 'var(--bg-subtle)',
          padding: '4px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '20px'
        }}>
          <button
            type="button"
            onClick={() => { setTab('login'); setError(null); }}
            style={{
              flex: 1,
              padding: '8px 12px',
              fontSize: '0.85rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: tab === 'login' ? '#ffffff' : 'transparent',
              color: tab === 'login' ? 'var(--primary)' : 'var(--text-muted)',
              boxShadow: tab === 'login' ? 'var(--shadow-sm)' : 'none',
              transition: 'all 0.15s ease'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab('register'); setError(null); }}
            style={{
              flex: 1,
              padding: '8px 12px',
              fontSize: '0.85rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: tab === 'register' ? '#ffffff' : 'transparent',
              color: tab === 'register' ? 'var(--primary)' : 'var(--text-muted)',
              boxShadow: tab === 'register' ? 'var(--shadow-sm)' : 'none',
              transition: 'all 0.15s ease'
            }}
          >
            Register
          </button>
          <button
            type="button"
            onClick={() => { setTab('demo'); setError(null); }}
            style={{
              flex: 1,
              padding: '8px 12px',
              fontSize: '0.85rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: tab === 'demo' ? '#ffffff' : 'transparent',
              color: tab === 'demo' ? 'var(--primary)' : 'var(--text-muted)',
              boxShadow: tab === 'demo' ? 'var(--shadow-sm)' : 'none',
              transition: 'all 0.15s ease'
            }}
          >
            ⚡ Demo Roles
          </button>
        </div>

        {/* Error Notification */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
            padding: '10px 14px',
            backgroundColor: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--danger-text)',
            fontSize: '0.825rem',
            marginBottom: '16px'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>{error}</div>
          </div>
        )}

        {/* Login Form */}
        {tab === 'login' && (
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px', color: 'var(--text-main)' }}>
                Official Email
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-light)' }} />
                <input
                  type="email"
                  required
                  placeholder="investigator@police.gov"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px', color: 'var(--text-main)' }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-light)' }} />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', padding: '11px' }}
            >
              {loading ? "Authenticating..." : "Sign In with Firebase"}
              <LogIn size={16} />
            </button>
          </form>
        )}

        {/* Register Form */}
        {tab === 'register' && (
          <form onSubmit={handleRegister}>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px', color: 'var(--text-main)' }}>
                Full Name & Rank
              </label>
              <div style={{ position: 'relative' }}>
                <User size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-light)' }} />
                <input
                  type="text"
                  required
                  placeholder="Det. Marcus Vance"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px', color: 'var(--text-main)' }}>
                Agency Email
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-light)' }} />
                <input
                  type="email"
                  required
                  placeholder="m.vance@police.gov"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px', color: 'var(--text-main)' }}>
                Password (min 6 characters)
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-light)' }} />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-main)' }}>
                  Assigned Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="form-select"
                  style={{ fontSize: '0.82rem' }}
                >
                  <option value="LEAD_INVESTIGATOR">Lead Investigator</option>
                  <option value="INVESTIGATOR">Field Investigator</option>
                  <option value="FORENSIC_SPECIALIST">Forensic Specialist</option>
                  <option value="FINANCIAL_AUDITOR">Financial Auditor</option>
                  <option value="PROSECUTOR_JUDGE">Prosecutor / Judge</option>
                  <option value="ADMIN">System Admin</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-main)' }}>
                  Department
                </label>
                <select
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="form-select"
                  style={{ fontSize: '0.82rem' }}
                >
                  <option value="INVESTIGATION">Investigation</option>
                  <option value="FORENSICS">Forensics</option>
                  <option value="CYBER">Cyber & Digital</option>
                  <option value="FINANCIAL">Financial Crimes</option>
                  <option value="LEGAL">Legal & Judicial</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', padding: '11px' }}
            >
              {loading ? "Creating Account..." : "Register Officer Account"}
              <UserPlus size={16} />
            </button>
          </form>
        )}

        {/* Demo Roles 1-Click Fast Switcher */}
        {tab === 'demo' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Select an official role to inspect the pre-seeded theft investigation:
            </p>

            <button
              type="button"
              onClick={() => handleQuickLogin('lead@police.gov', 'LEAD_INVESTIGATOR', 'INVESTIGATION')}
              disabled={loading}
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  Lead Detective Harris
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Role: LEAD_INVESTIGATOR • Full Case Management
                </div>
              </div>
              <span className="badge badge-blue">Select</span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('forensic@police.gov', 'FORENSIC_SPECIALIST', 'FORENSICS')}
              disabled={loading}
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  Dr. Aris Thorne
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Role: FORENSIC_SPECIALIST • Physical Toolmarks & CCTV
                </div>
              </div>
              <span className="badge badge-purple">Select</span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('financial@police.gov', 'FINANCIAL_AUDITOR', 'FINANCIAL')}
              disabled={loading}
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  Auditor Claire Sterling
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Role: FINANCIAL_AUDITOR • Inventory & Payment Ledger
                </div>
              </div>
              <span className="badge badge-amber">Select</span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('judge@justice.gov', 'PROSECUTOR_JUDGE', 'LEGAL')}
              disabled={loading}
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  Magistrate Patricia Vance
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Role: PROSECUTOR_JUDGE • Evidentiary Dossier Review
                </div>
              </div>
              <span className="badge badge-green">Select</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
