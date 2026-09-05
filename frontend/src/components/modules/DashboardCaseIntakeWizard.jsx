import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Plus, 
  CheckCircle, 
  Info, 
  Upload, 
  Video, 
  Camera, 
  FileSpreadsheet, 
  FileText, 
  Trash2, 
  Sparkles, 
  AlertCircle,
  FileCheck,
  Building2,
  Calendar,
  Clock,
  MapPin
} from 'lucide-react';
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

export default function DashboardCaseIntakeWizard({ onCaseCreated, onCancel }) {
  // Section 1: Incident Identity
  const [title, setTitle] = useState('');
  const [offenseCategory, setOffenseCategory] = useState('THEFT');
  const [specificOffense, setSpecificOffense] = useState('SHOPLIFTING');
  const [incidentTime, setIncidentTime] = useState(new Date().toISOString().slice(0, 16));
  const [location, setLocation] = useState('');
  const [narrative, setNarrative] = useState('');
  const [objectives, setObjectives] = useState('Identify candidate actors, verify stock deficit, correlate camera coverage');

  // Section 2: Evidence Manifest Items
  const [exhibits, setExhibits] = useState([]);
  
  // Pending exhibit form state
  const [exhibitType, setExhibitType] = useState('CCTV'); // 'CCTV' | 'IMAGE' | 'INVENTORY_RECORD' | 'WITNESS_STATEMENT'
  const [exhibitFile, setExhibitFile] = useState(null);
  const [exhibitTitle, setExhibitTitle] = useState('');
  const [exhibitDesc, setExhibitDesc] = useState('');
  const [witnessText, setWitnessText] = useState('');

  // Submission State
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [error, setError] = useState(null);

  const handleCategoryChange = (cat) => {
    setOffenseCategory(cat);
    setSpecificOffense(OFFENSE_TYPES[cat][0].value);
  };

  const handleAddExhibit = (e) => {
    e?.preventDefault();
    if (!exhibitTitle.trim()) {
      setError('Please provide an exhibit title/label.');
      return;
    }

    if (exhibitType === 'WITNESS_STATEMENT' && !exhibitFile && witnessText.trim()) {
      // Create text blob for witness statement
      const blob = new Blob([witnessText], { type: 'text/plain' });
      const textFile = new File([blob], `${exhibitTitle.replace(/\s+/g, '_')}_statement.txt`, { type: 'text/plain' });
      
      const newEx = {
        id: `ex_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
        title: exhibitTitle.trim(),
        evidence_type: 'WITNESS_STATEMENT',
        department: 'INVESTIGATION',
        file: textFile,
        filename: textFile.name,
        size_bytes: textFile.size,
        description: exhibitDesc.trim() || 'Eyewitness testimony statement',
        source_modality: 'HUMAN_TESTIMONIAL'
      };
      setExhibits(prev => [...prev, newEx]);
    } else {
      if (!exhibitFile) {
        setError('Please choose a file to attach for this exhibit.');
        return;
      }
      
      let dept = 'INVESTIGATION';
      let modality = 'DOCUMENT';
      if (exhibitType === 'CCTV') {
        dept = 'INVESTIGATION';
        modality = 'MOVING_IMAGE_WITH_TIMECODE';
      } else if (exhibitType === 'IMAGE') {
        dept = 'FORENSIC';
        modality = 'STILL_PHOTOGRAPHY';
      } else if (exhibitType === 'INVENTORY_RECORD') {
        dept = 'FINANCIAL';
        modality = 'STRUCTURED_FINANCIAL_LEDGER';
      } else if (exhibitType === 'WITNESS_STATEMENT') {
        dept = 'INVESTIGATION';
        modality = 'HUMAN_TESTIMONIAL';
      }

      const newEx = {
        id: `ex_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
        title: exhibitTitle.trim(),
        evidence_type: exhibitType,
        department: dept,
        file: exhibitFile,
        filename: exhibitFile.name,
        size_bytes: exhibitFile.size,
        description: exhibitDesc.trim() || `${exhibitType} exhibit`,
        source_modality: modality
      };
      setExhibits(prev => [...prev, newEx]);
    }

    // Reset exhibit input
    setExhibitFile(null);
    setExhibitTitle('');
    setExhibitDesc('');
    setWitnessText('');
    setError(null);
  };

  const handleRemoveExhibit = (id) => {
    setExhibits(prev => prev.filter(ex => ex.id !== id));
  };

  const handleSubmitAll = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Please provide a Case Title.');
      return;
    }

    setLoading(true);
    setError(null);
    setProgressMsg('Registering case in database...');

    try {
      // 1. Create Case
      const casePayload = {
        title: title.trim(),
        case_type: offenseCategory,
        offense_category: offenseCategory,
        specific_offense: specificOffense,
        incident_location: location.trim() || 'General Scene Location',
        investigative_objectives: objectives.split(',').map(s => s.trim()).filter(Boolean),
        incident_time_observed: incidentTime ? new Date(incidentTime).toISOString() : new Date().toISOString()
      };

      const newCase = await api.cases.create(casePayload);
      const caseId = newCase.id;

      // 2. Upload Attached Exhibits
      if (exhibits.length > 0) {
        for (let i = 0; i < exhibits.length; i++) {
          const ex = exhibits[i];
          setProgressMsg(`Uploading & hashing exhibit ${i + 1} of ${exhibits.length}: ${ex.title}...`);
          
          const formData = new FormData();
          formData.append('file', ex.file);
          formData.append('title', ex.title);
          formData.append('description', ex.description);
          formData.append('source_type', ex.evidence_type);
          formData.append('department', ex.department);
          formData.append('custody_officer', 'Intake Specialist');

          await api.evidence.upload(caseId, formData);
        }
      }

      setProgressMsg('Case and evidence registered successfully! Launching case workspace...');
      if (onCaseCreated) {
        onCaseCreated(newCase);
      }
    } catch (err) {
      console.error("Case registration error:", err);
      setError(err.message || 'Failed to complete case intake.');
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="card" style={{ padding: '32px', borderColor: 'var(--primary-border)', backgroundColor: '#ffffff', boxShadow: 'var(--shadow-md)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-light)', paddingBottom: '20px', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="badge badge-blue">Case Intake Wizard</span>
            <span className="badge badge-purple">Multi-Department Evidence Manifest</span>
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '6px' }}>
            Register New Investigation Case & Intake Exhibits
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: '720px' }}>
            Structure the incident profile, specify the legal offense classification, and attach all available physical, visual, and financial exhibits directly to initialize the 45-engine reconstruction platform.
          </p>
        </div>

        {onCancel && (
          <button onClick={onCancel} className="btn btn-secondary">
            Cancel
          </button>
        )}
      </div>

      {error && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'var(--danger-bg)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--danger-text)',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '24px'
        }}>
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmitAll} style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        {/* ================================================================= */}
        {/* SECTION 1: WHAT IS THE INCIDENT? */}
        {/* ================================================================= */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: 'var(--primary)', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.85rem' }}>
              1
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Incident Profile & Legal Offense Classification
            </h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                Case Title / Incident Tag <span style={{ color: '#dc2626' }}>*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. Retail Electronics Stock Shortage - Store #402"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="form-input"
                style={{ width: '100%', fontSize: '0.95rem' }}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                Offense Category Domain
              </label>
              <div style={{ display: 'flex', gap: '12px' }}>
                {['THEFT', 'ROBBERY'].map(cat => (
                  <label 
                    key={cat}
                    style={{
                      flex: 1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-md)',
                      border: `1px solid ${offenseCategory === cat ? 'var(--primary)' : 'var(--border-light)'}`,
                      backgroundColor: offenseCategory === cat ? 'var(--bg-accent-light)' : '#ffffff',
                      cursor: 'pointer',
                      fontWeight: offenseCategory === cat ? 700 : 500,
                      color: offenseCategory === cat ? 'var(--primary)' : 'var(--text-main)'
                    }}
                  >
                    <input
                      type="radio"
                      name="offenseCategory"
                      value={cat}
                      checked={offenseCategory === cat}
                      onChange={() => handleCategoryChange(cat)}
                      style={{ display: 'none' }}
                    />
                    <span>{cat === 'THEFT' ? 'Theft / Larceny' : 'Robbery (Force / Coercion)'}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                Specific Offense Classification
              </label>
              <select
                value={specificOffense}
                onChange={(e) => setSpecificOffense(e.target.value)}
                className="form-input"
                style={{ width: '100%' }}
              >
                {OFFENSE_TYPES[offenseCategory].map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                Incident Date & Time (Approximate or Exact)
              </label>
              <input
                type="datetime-local"
                value={incidentTime}
                onChange={(e) => setIncidentTime(e.target.value)}
                className="form-input"
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                Incident Location / Premises
              </label>
              <input
                type="text"
                placeholder="e.g. 5th Ave Commercial District / Aisle 2"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="form-input"
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                Incident Summary & What Occurred
              </label>
              <textarea
                rows={3}
                placeholder="Describe initial facts: e.g. Customer approached high-value display shelf at 14:15, stayed 3 minutes. Discrepancy identified during shift change inventory audit with 2 missing items."
                value={narrative}
                onChange={(e) => setNarrative(e.target.value)}
                className="form-input"
                style={{ width: '100%', resize: 'vertical' }}
              />
            </div>
          </div>
        </div>

        {/* ================================================================= */}
        {/* SECTION 2: WHAT ARE THE THINGS / EVIDENCE AVAILABLE? */}
        {/* ================================================================= */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: 'var(--primary)', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.85rem' }}>
              2
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Evidence Manifest: What Are The Things & Exhibits?
            </h3>
          </div>

          <div style={{ backgroundColor: '#f8fafc', padding: '20px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', marginBottom: '20px' }}>
            <div style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px', color: 'var(--text-main)' }}>
              Add An Incident Exhibit / File
            </div>

            {/* Exhibit Type Buttons */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '16px' }}>
              <button
                type="button"
                onClick={() => setExhibitType('CCTV')}
                className={`btn btn-sm ${exhibitType === 'CCTV' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Video size={15} />
                CCTV / Optical Video (.mp4)
              </button>

              <button
                type="button"
                onClick={() => setExhibitType('IMAGE')}
                className={`btn btn-sm ${exhibitType === 'IMAGE' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Camera size={15} />
                Physical / Damage Photo (.jpg, .png)
              </button>

              <button
                type="button"
                onClick={() => setExhibitType('INVENTORY_RECORD')}
                className={`btn btn-sm ${exhibitType === 'INVENTORY_RECORD' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <FileSpreadsheet size={15} />
                Inventory / POS Ledger (.csv)
              </button>

              <button
                type="button"
                onClick={() => setExhibitType('WITNESS_STATEMENT')}
                className={`btn btn-sm ${exhibitType === 'WITNESS_STATEMENT' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <FileText size={15} />
                Eyewitness Statement (.txt / narrative)
              </button>
            </div>

            {/* Exhibit Inputs */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px', marginBottom: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>
                  Exhibit Title / Identifier
                </label>
                <input
                  type="text"
                  placeholder={
                    exhibitType === 'CCTV' ? "e.g. Camera 02 - Aisle View" :
                    exhibitType === 'IMAGE' ? "e.g. Door Latch Damage Close-up" :
                    exhibitType === 'INVENTORY_RECORD' ? "e.g. Daily Shrinkage Reconciliation CSV" :
                    "e.g. Eyewitness Statement - Store Clerk"
                  }
                  value={exhibitTitle}
                  onChange={(e) => setExhibitTitle(e.target.value)}
                  className="form-input"
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>
                  Location / Context Note
                </label>
                <input
                  type="text"
                  placeholder="e.g. High-value electronics aisle / Rear loading dock"
                  value={exhibitDesc}
                  onChange={(e) => setExhibitDesc(e.target.value)}
                  className="form-input"
                  style={{ width: '100%' }}
                />
              </div>

              {exhibitType === 'WITNESS_STATEMENT' ? (
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>
                    Witness Statement Text (or attach .txt file below)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Enter eyewitness narrative: e.g. Saw individual wearing dark navy jacket lingering near display at 14:10..."
                    value={witnessText}
                    onChange={(e) => setWitnessText(e.target.value)}
                    className="form-input"
                    style={{ width: '100%', resize: 'vertical' }}
                  />
                </div>
              ) : null}

              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>
                  Select File Artifact {exhibitType === 'WITNESS_STATEMENT' ? '(Optional if text entered above)' : ''}
                </label>
                <input
                  type="file"
                  onChange={(e) => setExhibitFile(e.target.files[0] || null)}
                  className="form-input"
                  style={{ width: '100%', backgroundColor: '#ffffff' }}
                  accept={
                    exhibitType === 'CCTV' ? "video/*,.mp4,.mov,.avi,.mkv" :
                    exhibitType === 'IMAGE' ? "image/*,.jpg,.jpeg,.png,.tiff" :
                    exhibitType === 'INVENTORY_RECORD' ? ".csv,.json,.xlsx,.tsv" :
                    ".txt,.pdf,.doc,.docx"
                  }
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleAddExhibit}
              className="btn btn-outline"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <Plus size={16} />
              Attach This Exhibit to Manifest
            </button>
          </div>

          {/* Attached Exhibits Table / Cards */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Attached Exhibits ({exhibits.length})
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                All exhibits will receive SHA-256 integrity sealing on intake
              </span>
            </div>

            {exhibits.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', border: '1px dashed var(--border-light)', borderRadius: 'var(--radius-md)', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No exhibits attached yet. You can attach CCTV videos, damage photos, inventory CSVs, or witness statements above. (You can also add more later in the Evidence Vault).
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {exhibits.map((ex, idx) => (
                  <div
                    key={ex.id}
                    style={{
                      padding: '12px 16px',
                      backgroundColor: '#ffffff',
                      border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '12px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '8px',
                        backgroundColor: 'var(--bg-accent-light)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--primary)'
                      }}>
                        {ex.evidence_type === 'CCTV' ? <Video size={18} /> :
                         ex.evidence_type === 'IMAGE' ? <Camera size={18} /> :
                         ex.evidence_type === 'INVENTORY_RECORD' ? <FileSpreadsheet size={18} /> :
                         <FileText size={18} />}
                      </div>

                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                          {ex.title}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {ex.filename} ({formatBytes(ex.size_bytes)}) • {ex.description}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className="badge badge-blue">
                        {ex.department}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveExhibit(ex.id)}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '6px', color: '#dc2626' }}
                        title="Remove exhibit"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ================================================================= */}
        {/* SECTION 3: SUBMIT & DISPATCH */}
        {/* ================================================================= */}
        <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '24px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          <div>
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary)', fontSize: '0.85rem', fontWeight: 600 }}>
                <Sparkles size={16} className="animate-spin" />
                <span>{progressMsg}</span>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                disabled={loading}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            )}

            <button
              type="submit"
              disabled={loading || !title.trim()}
              className="btn btn-primary"
              style={{ minWidth: '220px', padding: '12px 24px', fontSize: '0.95rem' }}
            >
              <Sparkles size={18} />
              {loading ? 'Registering & Ingesting...' : `Register Case (${exhibits.length} Exhibits)`}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
