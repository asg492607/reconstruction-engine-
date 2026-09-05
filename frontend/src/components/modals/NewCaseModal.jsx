import React, { useState } from 'react';
import { X, ShieldAlert, Plus, CheckCircle, Info } from 'lucide-react';
import { api } from '../../api';

const OFFENSE_TYPES = {
  THEFT: [
    { value: 'SHOPLIFTING', label: 'Retail Shoplifting' },
    { value: 'EMPLOYEE_THEFT', label: 'Internal / Employee Theft' },
    { value: 'BURGLARY_THEFT', label: 'Commercial / Residential Burglary' },
    { value: 'VEHICLE_THEFT', label: 'Vehicle Theft' },
    { value: 'CARGO_THEFT', label: 'Cargo / Transit Theft' },
    { value: 'PACKAGE_THEFT', label: 'Package / Delivery Theft' },
    { value: 'EQUIPMENT_THEFT', label: 'Industrial / Construction Equipment' },
    { value: 'OTHER_PROPERTY_THEFT', label: 'Other Property Theft' }
  ],
  ROBBERY: [
    { value: 'COMMERCIAL_ROBBERY', label: 'Commercial Establishment Robbery' },
    { value: 'STREET_ROBBERY', label: 'Street / Mugging Robbery' },
    { value: 'HOME_ROBBERY', label: 'Home Invasion / Residential Robbery' },
    { value: 'VEHICLE_ROBBERY', label: 'Carjacking / Vehicle Robbery' },
    { value: 'ARMED_ROBBERY', label: 'Armed Robbery (Weapon Displayed)' },
    { value: 'UNARMED_ROBBERY', label: 'Strong-Arm / Unarmed Robbery' },
    { value: 'OTHER_ROBBERY', label: 'Other Robbery Offense' }
  ]
};

export default function NewCaseModal({ isOpen, onClose, onCaseCreated }) {
  const [offenseCategory, setOffenseCategory] = useState('THEFT');
  const [specificOffense, setSpecificOffense] = useState('SHOPLIFTING');
  const [title, setTitle] = useState('');
  const [location, setLocation] = useState('');
  const [objectives, setObjectives] = useState('Identify candidate actors, verify stock deficit, correlate camera coverage');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleCategoryChange = (cat) => {
    setOffenseCategory(cat);
    setSpecificOffense(OFFENSE_TYPES[cat][0].value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Please provide a case title.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload = {
        title: title.trim(),
        case_type: offenseCategory,
        offense_category: offenseCategory,
        specific_offense: specificOffense,
        incident_location: location.trim() || 'General Precinct Area',
        investigative_objectives: objectives.split(',').map(s => s.trim()).filter(Boolean),
        incident_time_observed: new Date().toISOString()
      };

      const newCase = await api.cases.create(payload);
      if (onCaseCreated) {
        onCaseCreated(newCase);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create case');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '560px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        border: '1px solid var(--border-light)',
        overflow: 'hidden',
        animation: 'fadeIn 0.2s ease-out'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          color: '#ffffff'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: 'rgba(37, 99, 235, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <ShieldAlert size={20} color="#60a5fa" />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>Register New Investigation Case</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>45-Engine Backbone Dynamic Capability Allocation</div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '24px' }}>
          {error && (
            <div style={{
              marginBottom: '16px',
              padding: '10px 14px',
              borderRadius: '8px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              fontSize: '0.825rem'
            }}>
              {error}
            </div>
          )}

          {/* Offense Category Radio / Toggle */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
              OFFENSE CATEGORY
            </label>
            <div style={{ display: 'flex', gap: '10px' }}>
              {['THEFT', 'ROBBERY'].map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => handleCategoryChange(cat)}
                  style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: '8px',
                    border: offenseCategory === cat ? '2px solid var(--primary)' : '1px solid var(--border-light)',
                    backgroundColor: offenseCategory === cat ? 'var(--bg-accent-light)' : '#ffffff',
                    color: offenseCategory === cat ? 'var(--primary)' : 'var(--text-muted)',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  {offenseCategory === cat && <CheckCircle size={15} color="var(--primary)" />}
                  {cat === 'THEFT' ? 'Theft Offense' : 'Robbery Offense'}
                </button>
              ))}
            </div>
          </div>

          {/* Specific Offense Subtype */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
              SPECIFIC OFFENSE SUBTYPE
            </label>
            <select
              value={specificOffense}
              onChange={(e) => setSpecificOffense(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-light)',
                backgroundColor: '#ffffff',
                fontSize: '0.85rem',
                color: 'var(--text-main)',
                fontWeight: 600,
                outline: 'none'
              }}
            >
              {OFFENSE_TYPES[offenseCategory].map((sub) => (
                <option key={sub.value} value={sub.value}>
                  {sub.label}
                </option>
              ))}
            </select>
          </div>

          {/* Case Title */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
              CASE TITLE / SUMMARY *
            </label>
            <input
              type="text"
              placeholder="e.g. Oakridge Mall Electronics Shortage & Unrecorded Exit"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-light)',
                fontSize: '0.85rem',
                color: 'var(--text-main)',
                outline: 'none'
              }}
              required
            />
          </div>

          {/* Incident Location */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
              INCIDENT PREMISES / LOCATION
            </label>
            <input
              type="text"
              placeholder="e.g. 742 Evergreen Terrace, Storefront B4"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-light)',
                fontSize: '0.85rem',
                color: 'var(--text-main)',
                outline: 'none'
              }}
            />
          </div>

          {/* Investigative Objectives */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
              INVESTIGATIVE OBJECTIVES (COMMA SEPARATED)
            </label>
            <textarea
              rows={2}
              value={objectives}
              onChange={(e) => setObjectives(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-light)',
                fontSize: '0.825rem',
                color: 'var(--text-main)',
                outline: 'none',
                resize: 'none'
              }}
            />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '9px 16px',
                borderRadius: '8px',
                border: '1px solid var(--border-light)',
                backgroundColor: '#ffffff',
                color: 'var(--text-muted)',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '9px 20px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.2)'
              }}
            >
              <Plus size={16} />
              {loading ? 'Registering...' : 'Create Case & Initialize Backbone'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
