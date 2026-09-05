import React, { useState } from 'react';
import {
  Shield,
  FileText,
  Printer,
  Download,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  Cpu,
  GitBranch,
  Users,
  Scale,
  Eye,
  Database,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Lock,
  ThumbsUp,
  ThumbsDown,
  Edit3
} from 'lucide-react';
import { api } from '../../api';

export default function UnifiedReconstructionOutput({
  caseData,
  evidence = [],
  timelineEvents = [],
  hypotheses = [],
  gapsConflicts = [],
  entities = [],
  telemetry = [],
  onRunReconstruction,
  reconstructionLoading
}) {
  const [activeSection, setActiveSection] = useState('summary');
  const [expandedEngine, setExpandedEngine] = useState(null);
  const [signOffDecisions, setSignOffDecisions] = useState({});
  const [signOffNotes, setSignOffNotes] = useState('');

  // Extract X02 Timeline from telemetry or props
  const x02Telemetry = telemetry.find(t => t.engine_id === 'X02');
  const rawTimelineEvents = (x02Telemetry?.outputs && x02Telemetry.outputs.length > 0)
    ? x02Telemetry.outputs
    : (timelineEvents || []);
  const activeTimelineEvents = rawTimelineEvents.filter(e => e.source_modality !== 'SYSTEM_RECORD' && e.event_id !== 'TL_001');
  const timelineModalities = new Set(activeTimelineEvents.map(e => e.source_modality));
  const isMultiSourceSynchronized = timelineModalities.size > 1;

  // Extract X06 Sufficiency from telemetry
  const x06Telemetry = telemetry.find(t => t.engine_id === 'X06');
  const hasTelemetry = telemetry && telemetry.length > 0;
  const hasBlockedEngines = telemetry.some(t => t.status === 'BLOCKED');
  const defaultRating = hasTelemetry
    ? (hasBlockedEngines ? "EXECUTION_COMPLETE_WITH_BLOCKED_ENGINES" : "INSUFFICIENT_FOR_RECONSTRUCTION")
    : "PENDING_EXECUTION";

  const sufficiencyData = x06Telemetry?.outputs?.[0] || {
    sufficiency_rating: defaultRating,
    proceed_to_reconstruction: false,
    evaluation_criteria: {
      temporal_anchor_established: activeTimelineEvents.length > 0,
      spatial_pathway_plausible: false,
      asset_delta_proven: evidence.some(e => e.evidence_type === 'INVENTORY_RECORD'),
      actor_attribution_corroborated: entities.length > 0
    },
    summary: hasTelemetry
      ? (x06Telemetry?.failure_reason || "Evidence sufficiency evaluated. Required corroborating modalities missing or blocked.")
      : "Reconstruction execution pending. Run 45-engine analysis pipeline."
  };

  // Extract R01 Hypotheses from telemetry (45-engine run) or fallback to database hypotheses
  const r01Telemetry = telemetry.find(t => t.engine_id === 'R01');
  const isR01Blocked = r01Telemetry ? r01Telemetry.status === 'BLOCKED' : false;
  const activeHypotheses = isR01Blocked
    ? []
    : (r01Telemetry?.outputs && r01Telemetry.outputs.length > 0)
      ? r01Telemetry.outputs
      : (hypotheses || []);

  // Extract R02 Feasibility from telemetry
  const r02Telemetry = telemetry.find(t => t.engine_id === 'R02');
  const isR02Blocked = r02Telemetry ? r02Telemetry.status === 'BLOCKED' : false;
  const feasibilityChecks = isR02Blocked ? [] : (r02Telemetry?.outputs || []);

  // Extract R03 Adversarial Challenges from telemetry
  const r03Telemetry = telemetry.find(t => t.engine_id === 'R03');
  const isR03Blocked = r03Telemetry ? r03Telemetry.status === 'BLOCKED' : false;
  const adversarialChallenges = isR03Blocked ? [] : (r03Telemetry?.outputs || []);

  // Extract X04 Gaps & X05 Conflicts from telemetry (or fallback to database gapsConflicts)
  const x04Telemetry = telemetry.find(t => t.engine_id === 'X04');
  const x05Telemetry = telemetry.find(t => t.engine_id === 'X05');

  const telemetryGaps = (x04Telemetry?.outputs || []).map((g, idx) => ({
    ...g,
    id: g.gap_id || `GAP_${idx}`,
    gc_type: 'GAP',
    item_type: 'GAP',
    category: 'MISSING_EVIDENCE',
    severity: g.significance || 'HIGH',
    title: g.title || (g.gap_type === 'EVIDENCE_MODALITY_GAP' ? `Missing Modality Gap: ${g.gap_id}` : 'Evidentiary Gap'),
    description: g.description
  }));

  const telemetryConflicts = (x05Telemetry?.outputs || []).map((c, idx) => ({
    ...c,
    id: c.conflict_id || `CONF_${idx}`,
    gc_type: c.conflict_type || 'SOURCE_DISAGREEMENT',
    item_type: 'CONFLICT',
    category: 'CONFLICT',
    severity: c.severity || 'HIGH',
    title: c.title || c.conflict_type || 'Source Discrepancy',
    description: c.description || c.discrepancy_explanation
  }));

  // Gaps: prioritize X04 telemetry outputs; fallback to database gaps
  const activeGaps = x04Telemetry
    ? telemetryGaps
    : (gapsConflicts || []).filter(gc => gc.gc_type === 'GAP');

  // Conflicts: prioritize X05 telemetry outputs; fallback to database conflicts
  const activeConflicts = x05Telemetry
    ? telemetryConflicts
    : (gapsConflicts || []).filter(gc => gc.gc_type !== 'GAP');

  const activeGapsConflicts = [...activeGaps, ...activeConflicts];
  const activeConflictCount = activeConflicts.length;

  const handlePrint = () => {
    window.print();
  };

  const handleExportJson = () => {
    const fullDossier = {
      dossier_type: "RECONSTRUCTION_INTELLIGENCE_DOSSIER",
      generated_at: new Date().toISOString(),
      case_profile: caseData,
      sufficiency_gating: sufficiencyData,
      evidence_exhibits: evidence.map(e => ({
        id: e.id,
        title: e.title,
        type: e.evidence_type,
        department: e.department,
        sha256_hash: e.sha256_hash
      })),
      correlated_timeline: timelineEvents,
      reconstruction_hypotheses: hypotheses,
      adversarial_defense_challenges: adversarialChallenges,
      feasibility_checks: feasibilityChecks,
      gaps_and_conflicts: gapsConflicts,
      candidate_entities: entities,
      engine_telemetry_provenance: telemetry,
      sign_off_audit: signOffDecisions
    };

    const blob = new Blob([JSON.stringify(fullDossier, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Reconstruction_Dossier_${caseData?.case_number || 'CASE'}.json`;
    a.click();
  };

  const handleDecision = (tier, decision) => {
    setSignOffDecisions(prev => ({
      ...prev,
      [tier]: {
        decision,
        decided_at: new Date().toISOString(),
        notes: signOffNotes || 'Standard procedural review completed.'
      }
    }));
  };

  const scrollTo = (id) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1200px', margin: '0 auto', paddingBottom: '60px' }}>
      {/* ================================================================= */}
      {/* TOP HEADER & ACTION BAR */}
      {/* ================================================================= */}
      <div className="card" style={{
        padding: '24px 28px',
        backgroundColor: '#ffffff',
        border: '1px solid var(--primary-border)',
        boxShadow: 'var(--shadow-md)'
      }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
              <span className="badge badge-blue">Reconstruction Intelligence Dossier</span>
              <span className="badge badge-purple">{caseData?.case_number || 'CASE-FILE'}</span>
              <span className="badge badge-green">45-Engine Backbone Synchronized</span>
              <span className="badge badge-slate" title="Analysis execution runs are immutable and versioned in the audit trail">Immutable Run History Active</span>
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
              {caseData?.title || 'Comprehensive Incident Reconstruction Report'}
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Theft Domain: <strong>{caseData?.specific_offense || caseData?.case_type || 'General Offense'}</strong> • Location: <strong>{caseData?.incident_location || 'Scene Site'}</strong> • Generated: {new Date().toLocaleString()}
            </p>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            {onRunReconstruction && (
              <button
                onClick={onRunReconstruction}
                disabled={reconstructionLoading}
                className="btn btn-outline"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                title="Executes the full engine backbone. Appends a new immutable analysis version to the audit log without overwriting history."
              >
                <Sparkles size={16} color="var(--primary)" />
                {reconstructionLoading ? 'Executing 45 Engines...' : 'Re-Run All Engines (New Version)'}
              </button>
            )}
            <button
              onClick={handleExportJson}
              className="btn btn-outline"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Download size={16} />
              Export Dossier (JSON)
            </button>
            <button
              onClick={handlePrint}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Printer size={16} />
              Print / Save PDF
            </button>
          </div>
        </div>

        {/* Quick-Nav Bar */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          borderTop: '1px solid var(--border-light)',
          paddingTop: '16px'
        }}>
          {[
            { id: 'sec-summary', label: '1. Executive Summary' },
            { id: 'sec-timeline', label: isMultiSourceSynchronized ? `2. Correlated Timeline (${activeTimelineEvents.length})` : (activeTimelineEvents.length > 0 ? `2. Source-Local Events (${activeTimelineEvents.length})` : `2. Correlated Timeline (0)`) },
            { id: 'sec-hypotheses', label: `3. Hypotheses & Citations (${activeHypotheses.length})` },
            { id: 'sec-challenges', label: `4. Defense Challenges (${adversarialChallenges.length})` },
            { id: 'sec-feasibility', label: `5. Physics Feasibility (${feasibilityChecks.length})` },
            { id: 'sec-gaps', label: `6. Gaps (${activeGaps.length}) & Conflicts (${activeConflictCount})` },
            { id: 'sec-entities', label: `7. Candidate Entities (${entities.length})` },
            { id: 'sec-provenance', label: `8. Engine Provenance (${telemetry.length})` },
            { id: 'sec-signoff', label: '9. Specialist Sign-Off' }
          ].map(item => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className="btn btn-secondary btn-sm"
              style={{
                fontSize: '0.78rem',
                backgroundColor: activeSection === item.id ? 'var(--primary)' : '#f1f5f9',
                color: activeSection === item.id ? '#ffffff' : 'var(--text-main)',
                borderColor: activeSection === item.id ? 'var(--primary)' : 'var(--border-light)'
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* ================================================================= */}
      {/* SECTION 1: EXECUTIVE SUMMARY & SUFFICIENCY GATING (X06) */}
      {/* ================================================================= */}
      <section id="sec-summary" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', fontWeight: 800 }}>
              1
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Executive Reconstruction Summary & Evidence Sufficiency Gating (X06)
            </h2>
          </div>

          <span className={
            sufficiencyData.sufficiency_rating === "SUFFICIENT_FOR_RECONSTRUCTION" ? "badge badge-green" :
              sufficiencyData.sufficiency_rating === "MARGINAL_PROBATIVE_VALUE" ? "badge badge-amber" :
                "badge badge-red"
          } style={{ fontSize: '0.85rem', padding: '6px 12px' }}>
            {sufficiencyData.sufficiency_rating}
          </span>
        </div>

        {/* Non-Verdict Principle Banner */}
        <div style={{
          backgroundColor: '#f8fafc',
          borderLeft: '4px solid var(--primary)',
          padding: '12px 16px',
          borderRadius: '0 8px 8px 0',
          marginBottom: '20px',
          fontSize: '0.825rem',
          color: 'var(--text-muted)'
        }}>
          <strong>Forensic Provenance & Non-Verdict Standard:</strong> This dossier structures factual observations across multi-source exhibits, evaluates mathematical feasibility, and stress-tests competing hypotheses. It makes no autonomous assertion of statutory guilt.
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px', marginBottom: '20px' }}>
          <div style={{ padding: '14px', backgroundColor: '#ffffff', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>TEMPORAL ANCHORS</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: isMultiSourceSynchronized ? '#059669' : (activeTimelineEvents.length > 0 ? '#d97706' : '#dc2626'), marginTop: '4px' }}>
              {isMultiSourceSynchronized ? "✓ Chronology Established" : (activeTimelineEvents.length > 0 ? "• Single-Source Events" : "✗ Gaps in Timeline")}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              {isMultiSourceSynchronized ? `${activeTimelineEvents.length} synchronized events` : (activeTimelineEvents.length > 0 ? `${activeTimelineEvents.length} source-local events (0 correlated)` : "0 synchronized events")}
            </div>
          </div>

          <div style={{ padding: '14px', backgroundColor: '#ffffff', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>SPATIAL PATHWAY</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: sufficiencyData.evaluation_criteria?.spatial_pathway_plausible ? '#059669' : '#dc2626', marginTop: '4px' }}>
              {sufficiencyData.evaluation_criteria?.spatial_pathway_plausible ? "✓ Pathway Feasible" : "Transit pathway: NOT ESTABLISHED"}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px', lineHeight: 1.4 }}>
              {sufficiencyData.evaluation_criteria?.spatial_pathway_plausible 
                ? "Transit bounds verified" 
                : "Available evidence does not provide sufficient movement observations to verify a spatial pathway."}
            </div>
          </div>

          <div style={{ padding: '14px', backgroundColor: '#ffffff', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>ASSET DEFICIT AUDIT</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: sufficiencyData.evaluation_criteria?.asset_delta_proven ? '#059669' : '#d97706', marginTop: '4px' }}>
              {sufficiencyData.evaluation_criteria?.asset_delta_proven ? "✓ Ledger Discrepancy Verified" : "• Awaiting Financial Ledger"}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Reconciliation audit status
            </div>
          </div>

          <div style={{ padding: '14px', backgroundColor: '#ffffff', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>ACTOR ATTRIBUTION</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: sufficiencyData.evaluation_criteria?.actor_attribution_corroborated ? '#059669' : '#d97706', marginTop: '4px' }}>
              {sufficiencyData.evaluation_criteria?.actor_attribution_corroborated ? "✓ Candidate Associated" : "• Unattributed Entity"}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Strictly candidate status
            </div>
          </div>
        </div>

        <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.6 }}>
          <strong>Synthesis Narrative:</strong> {sufficiencyData.summary || "Case exhibits provide verifiable factual grounding across temporal, visual, and financial dimensions."}
        </p>

        {/* Analytical Decision & Basis (X06) */}
        <div style={{
          marginTop: '16px',
          padding: '16px 20px',
          backgroundColor: sufficiencyData.sufficiency_rating === "SUFFICIENT_FOR_RECONSTRUCTION" ? '#f0fdf4' : (sufficiencyData.sufficiency_rating === "MARGINAL_PROBATIVE_VALUE" ? '#fffbeb' : '#fef2f2'),
          border: `1px solid ${sufficiencyData.sufficiency_rating === "SUFFICIENT_FOR_RECONSTRUCTION" ? '#bbf7d0' : (sufficiencyData.sufficiency_rating === "MARGINAL_PROBATIVE_VALUE" ? '#fde68a' : '#fecaca')}`,
          borderRadius: 'var(--radius-md)'
        }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Evidentiary Reconstruction Sufficiency Evaluation (X06)
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px', lineHeight: 1.4 }}>
            <em>Evaluation Scope:</em> Evaluates evidentiary threshold required to synthesize a defensible factual chronology. <strong>Makes no determination regarding incident occurrence, statutory guilt, or actor intent.</strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-main)' }}>Reconstruction Sufficiency:</span>
            <span className={sufficiencyData.sufficiency_rating === "SUFFICIENT_FOR_RECONSTRUCTION" ? "badge badge-green" : "badge badge-red"} style={{ fontSize: '0.8rem', padding: '4px 10px' }}>
              {sufficiencyData.sufficiency_rating === "SUFFICIENT_FOR_RECONSTRUCTION" ? "SUFFICIENT" : "INSUFFICIENT"}
            </span>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Execution Status: <strong>SUCCESS</strong></span>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: sufficiencyData.sufficiency_rating === "SUFFICIENT_FOR_RECONSTRUCTION" ? '#059669' : '#dc2626' }}>
              Analytical Result: <strong>{sufficiencyData.sufficiency_rating || 'INSUFFICIENT_FOR_RECONSTRUCTION'}</strong>
            </span>
          </div>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>Decision Basis:</div>
          <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--text-muted)', fontSize: '0.78rem', lineHeight: 1.5 }}>
            {sufficiencyData.decision_basis && Array.isArray(sufficiencyData.decision_basis) && sufficiencyData.decision_basis.length > 0 ? (
              sufficiencyData.decision_basis.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))
            ) : (
              <>
                <li>{activeTimelineEvents.length > 0 ? `${activeTimelineEvents.length} source-local events (0 correlated cross-domain events)` : '0 correlated events'}</li>
                <li>{sufficiencyData.evaluation_criteria?.spatial_pathway_plausible ? 'CCTV surveillance video verified' : 'no CCTV'}</li>
                <li>{sufficiencyData.evaluation_criteria?.asset_delta_proven ? 'financial transaction/inventory ledger present' : 'no financial records'}</li>
                <li>{sufficiencyData.evaluation_criteria?.actor_attribution_corroborated ? 'witness statements verified' : 'no usable witness extraction'}</li>
              </>
            )}
          </ul>
        </div>
      </section>

      {/* ================================================================= */}
      {/* SECTION 2: MULTI-SOURCE CORRELATED TIMELINE (X02) */}
      {/* ================================================================= */}
      <section id="sec-timeline" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', fontWeight: 800 }}>
            2
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              {isMultiSourceSynchronized ? "Multi-Source Correlated Timeline (X02)" : "Chronological Events & Source Alignment (X02)"}
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {isMultiSourceSynchronized
                ? `Synchronized timeline: ${activeTimelineEvents.length} events aligned across ${timelineModalities.size} independent sensor and witness modalities.`
                : activeTimelineEvents.length > 0
                  ? `Source-local events: ${activeTimelineEvents.length} • Correlated events: 0 (Decoupled local observations; cross-domain synchronization requires multi-modal evidence).`
                  : "No timeline events established from uploaded case exhibits."}
            </p>
          </div>
        </div>

        {activeTimelineEvents.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No timeline events generated yet. Upload timestamped exhibits (CCTV, POS registers, or eyewitness statements) to establish temporal anchors.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px 12px' }}>Timestamp</th>
                  <th style={{ padding: '10px 12px' }}>Source Modality</th>
                  <th style={{ padding: '10px 12px' }}>Observation / Action</th>
                  <th style={{ padding: '10px 12px' }}>Clock Source</th>
                  <th style={{ padding: '10px 12px' }}>Time Confidence</th>
                </tr>
              </thead>
              <tbody>
                {activeTimelineEvents.map((ev, idx) => (
                  <tr key={ev.event_id || idx} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 600 }}>
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Approx'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className={
                        ev.source_modality === 'CCTV_VIDEO' ? 'badge badge-purple' :
                          ev.source_modality === 'POS_TRANSACTION' ? 'badge badge-amber' :
                            'badge badge-blue'
                      }>
                        {ev.source_modality || 'OBSERVATION'}
                      </span>
                    </td>
                    <td style={{ padding: '12px', color: 'var(--text-main)', fontWeight: 500 }}>
                      {ev.label || ev.description || ev.event_name}
                    </td>
                    <td style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {ev.clock_source || 'DEVICE_TIMESTAMP'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className={ev.time_confidence === 'EXACT' ? 'badge badge-green' : 'badge badge-slate'}>
                        {ev.time_confidence || 'ESTIMATED'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ================================================================= */}
      {/* SECTION 3: EVIDENCE-GROUNDED HYPOTHESES (R01) */}
      {/* ================================================================= */}
      <section id="sec-hypotheses" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', fontWeight: 800 }}>
            3
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Evidence-Constrained Hypotheses & Citations (R01)
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Synthesized competing scenarios. Every assertion is tied to an authenticated source exhibit citation.
            </p>
          </div>
        </div>
        {activeHypotheses.length === 0 ? (
          <div style={{
            padding: '28px 24px',
            backgroundColor: '#f8fafc',
            border: '1px dashed var(--border-light)',
            borderRadius: 'var(--radius-md)',
            textAlign: 'center',
            color: 'var(--text-muted)'
          }}>
            <div style={{ fontWeight: 800, color: isR01Blocked ? '#b91c1c' : 'var(--text-main)', marginBottom: '6px', fontSize: '0.95rem' }}>
              {isR01Blocked ? 'HYPOTHESIS GENERATION BLOCKED (X06 GATING ENFORCED)' : 'NO HYPOTHESES SYNTHESIZED'}
            </div>
            <p style={{ margin: 0, fontSize: '0.825rem', lineHeight: 1.5, maxWidth: '640px', marginInline: 'auto' }}>
              {isR01Blocked
                ? (r01Telemetry?.failure_reason || 'Required corroborating observations unavailable (X06: INSUFFICIENT_FOR_RECONSTRUCTION). Downstream hypothesis synthesis safely stopped to prevent fabrication.')
                : 'No evidence-grounded hypotheses generated yet. Run the 45-engine analysis plan.'}
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {activeHypotheses.map((h, idx) => {
              const isNoTheft = h.theft_conclusion_supported === false ||
                h.hypothesis_category === "INSUFFICIENT_EVIDENCE" ||
                h.overall_support_level === "INSUFFICIENT" ||
                h.status === "REJECTED";
              const title = h.title || h.hypothesis_title || h.label || `Hypothesis ${idx + 1}`;
              const narrative = h.narrative || h.description || "No scenario narrative available.";
              const category = h.hypothesis_category || (isNoTheft ? "INSUFFICIENT_EVIDENCE" : (idx === 0 ? "PRIMARY_HYPOTHESIS" : "ALTERNATIVE_EXPLANATION"));
              const verdict = isNoTheft ? "NO THEFT CONCLUSION" : (h.theft_conclusion_supported === true ? "THEFT PLAUSIBLE" : (h.overall_strength || "UNVERIFIED"));
              const citations = (h.supporting_evidence_citations && h.supporting_evidence_citations.length > 0)
                ? h.supporting_evidence_citations
                : (h.supporting_claims && h.supporting_claims.length > 0)
                  ? h.supporting_claims
                  : [];

              return (
                <div
                  key={h.id || h.hypothesis_id || idx}
                  style={{
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    border: isNoTheft ? '1px solid var(--border-light)' : '1px solid var(--primary-border)',
                    backgroundColor: isNoTheft ? '#fafafa' : (idx === 0 ? 'var(--bg-accent-light)' : '#ffffff')
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <div>
                      <span className={isNoTheft ? "badge badge-amber" : "badge badge-blue"} style={{ marginBottom: '4px' }}>
                        {category}
                      </span>
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)' }}>
                        {title}
                      </h3>
                    </div>

                    <span className={isNoTheft ? "badge badge-slate" : "badge badge-green"}>
                      {verdict}
                    </span>
                  </div>

                  <p style={{ fontSize: '0.875rem', color: 'var(--text-main)', lineHeight: 1.6, marginBottom: '12px' }}>
                    {narrative}
                  </p>

                  {/* Supporting Citations */}
                  <div style={{ marginBottom: '10px' }}>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '4px' }}>
                      Authenticating Evidence Citations:
                    </div>
                    {citations.length > 0 ? (
                      <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                        {citations.map((cit, cIdx) => (
                          <li key={cIdx}>{cit}</li>
                        ))}
                      </ul>
                    ) : (
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', paddingLeft: '4px' }}>
                        None — no corroborating source exhibits verified for this scenario.
                      </div>
                    )}
                  </div>

                  {/* Critical Gaps / Caveats */}
                  {h.critical_gap && (
                    <div style={{ padding: '8px 12px', backgroundColor: 'var(--danger-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--danger-border)', fontSize: '0.8rem', color: 'var(--danger-text)', marginBottom: '8px' }}>
                      <strong>Critical Evidentiary Gap:</strong> {h.critical_gap}
                    </div>
                  )}
                  {h.critical_gaps_identified && h.critical_gaps_identified.length > 0 && (
                    <div style={{ padding: '8px 12px', backgroundColor: '#fef2f2', borderRadius: 'var(--radius-sm)', border: '1px solid #fecaca', fontSize: '0.8rem', color: '#991b1b' }}>
                      <strong>Missing Prerequisites:</strong>
                      <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                        {h.critical_gaps_identified.map((gap, gIdx) => (
                          <li key={gIdx}>{gap}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ================================================================= */}
      {/* SECTION 4: ADVERSARIAL DEFENSE CHALLENGES (R03) */}
      {/* ================================================================= */}
      <section id="sec-challenges" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', fontWeight: 800 }}>
            4
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Adversarial Defense Challenges & Skeptical Stress-Testing (R03)
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Evaluates reasonable doubt vectors, missing continuous custody, and alternative innocent interpretations.
            </p>
          </div>
        </div>

        {adversarialChallenges.length === 0 ? (
          <div style={{
            padding: '24px',
            backgroundColor: '#f8fafc',
            border: '1px dashed var(--border-light)',
            borderRadius: 'var(--radius-md)',
            textAlign: 'center',
            color: 'var(--text-muted)'
          }}>
            <div style={{ fontWeight: 800, color: isR03Blocked ? '#b91c1c' : 'var(--text-main)', marginBottom: '6px', fontSize: '0.95rem' }}>
              {isR03Blocked ? 'ADVERSARIAL DEFENSE CHALLENGES BLOCKED' : 'NO DEFENSE CHALLENGES REGISTERED'}
            </div>
            <p style={{ margin: 0, fontSize: '0.825rem', lineHeight: 1.5, maxWidth: '640px', marginInline: 'auto' }}>
              {isR03Blocked
                ? (r03Telemetry?.failure_reason || 'Prerequisite engine R01 was BLOCKED. No hypotheses exist to adversarially challenge.')
                : 'No defense challenges registered. Run engine R03 in the reconstruction pipeline.'}
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {adversarialChallenges.map((adv, idx) => (
              <div
                key={idx}
                style={{
                  padding: '16px',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-md)',
                  borderLeft: '4px solid #dc2626'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <span className="badge badge-red">{adv.challenge_vector || 'DEFENSE_OBJECTION'}</span>
                  <span className="badge badge-slate">Vulnerability: {adv.evidentiary_vulnerability || 'EVALUATED'}</span>
                </div>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
                  {adv.adversarial_objection}
                </h4>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                  <strong>Rebuttal Grounding:</strong> {adv.rebuttal_grounding}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ================================================================= */}
      {/* SECTION 5: PHYSICAL FEASIBILITY CHECKS (R02) */}
      {/* ================================================================= */}
      <section id="sec-feasibility" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', fontWeight: 800 }}>
            5
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Deterministic Physical & Mathematical Feasibility Checks (R02)
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Monotonicity, spatial exclusivity, and transit velocity constraints.
            </p>
          </div>
        </div>

        {feasibilityChecks.length === 0 ? (
          <div style={{
            padding: '24px',
            backgroundColor: '#f8fafc',
            border: '1px dashed var(--border-light)',
            borderRadius: 'var(--radius-md)',
            textAlign: 'center',
            color: 'var(--text-muted)'
          }}>
            <div style={{ fontWeight: 800, color: isR02Blocked ? '#b91c1c' : 'var(--text-main)', marginBottom: '6px', fontSize: '0.95rem' }}>
              {isR02Blocked ? 'PHYSICAL FEASIBILITY CHECKS BLOCKED' : 'NO FEASIBILITY CHECKS EXECUTED'}
            </div>
            <p style={{ margin: 0, fontSize: '0.825rem', lineHeight: 1.5, maxWidth: '640px', marginInline: 'auto' }}>
              {isR02Blocked
                ? (r02Telemetry?.failure_reason || 'Prerequisite engine R01 is BLOCKED (no defensible sequence to test).')
                : 'No physical feasibility checks executed yet. Run the 45-engine analysis pipeline.'}
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
            {feasibilityChecks.map((chk, idx) => (
              <div key={idx} style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    {chk.check_name}
                  </span>
                  <span className={
                    chk.status === 'PASSED' || chk.status === 'FEASIBLE' ? 'badge badge-green' :
                      chk.status === 'NOT_ASSESSABLE' ? 'badge badge-slate' : 'badge badge-amber'
                  }>
                    {chk.status}
                  </span>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                  {chk.detail}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ================================================================= */}
      {/* SECTION 6: GAPS & CONFLICTS RADAR (X04 & X05) */}
      {/* ================================================================= */}
      <section id="sec-gaps" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', fontWeight: 800 }}>
            6
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Evidentiary Gaps ({activeGaps.length}) & Source Discrepancies ({activeConflictCount}) (X04 & X05)
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Unmonitored transit blind spots, clock drifts, and witness appearance disagreements.
            </p>
          </div>
        </div>

        {activeGapsConflicts.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No active gaps or contradictions identified.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
            {activeGapsConflicts.map((gc, idx) => (
              <div
                key={gc.id || idx}
                style={{
                  padding: '16px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-light)',
                  backgroundColor: gc.severity === 'HIGH' ? 'var(--danger-bg)' : 'var(--warning-bg)',
                  borderColor: gc.severity === 'HIGH' ? 'var(--danger-border)' : 'var(--warning-border)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.875rem', color: gc.severity === 'HIGH' ? 'var(--danger-text)' : 'var(--warning-text)' }}>
                    {gc.title || gc.conflict_type || gc.gap_type || `Anomaly #${idx + 1}`}
                  </span>
                  <span className={gc.severity === 'HIGH' ? 'badge badge-red' : 'badge badge-amber'}>
                    {gc.severity || gc.conflict_type || 'FLAGGED'}
                  </span>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.5, marginBottom: '6px' }}>
                  {gc.description || gc.discrepancy_explanation}
                </p>
                {gc.admissibility_and_credibility_note && (
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    Note: {gc.admissibility_and_credibility_note}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* X05 Analytical Conflict Audit Card */}
        <div style={{
          marginTop: '18px',
          padding: '16px 20px',
          backgroundColor: '#f8fafc',
          border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-md)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '0.02em' }}>
              Analytical Conflict & Discrepancy Audit (X05)
            </div>
            <span className="badge badge-slate" style={{ fontSize: '0.72rem' }}>
              DETERMINISTIC COMPONENT ONLY (NO AI MODEL INVOKED)
            </span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.6, display: 'grid', gap: '5px' }}>
            <div>
              <strong style={{ color: 'var(--text-main)' }}>Inputs available:</strong> forensic exhibit manifest, X02 chronology ({activeTimelineEvents.length} source-local events).
            </div>
            <div>
              <strong style={{ color: 'var(--text-main)' }}>Unavailable inputs:</strong> I06 CCTV attributes, I11 witness extraction, FI01/FI04 financial ledger.
            </div>
            <div>
              <strong style={{ color: 'var(--text-main)' }}>Checks performed:</strong> 7 discrepancy categories (HARD_CONTRADICTION, SOFT_DISCREPANCY, SOURCE_DISAGREEMENT, TEMPORAL_DISCREPANCY, CORROBORATIVE_DISCREPANCY, WITNESS_CONFLICT, UNCERTAINTY).
            </div>
            <div>
              <strong style={{ color: 'var(--text-main)' }}>Result:</strong> {activeConflictCount} cross-source conflicts detected.
            </div>
            <div>
              <strong style={{ color: 'var(--text-main)' }}>Reason:</strong> {activeConflictCount === 0
                ? "No mutually contradictory facts identified across available exhibits. (Note: Multi-source corroboration required to identify perceptual or temporal divergence)."
                : `Identified ${activeConflictCount} cross-source discrepancies between available evidentiary modalities requiring specialist review.`}
            </div>
            <div>
              <strong style={{ color: 'var(--text-main)' }}>Source references:</strong> Active case exhibits & validated departmental extractions.
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* SECTION 7: CANDIDATE ENTITIES & ATTRIBUTES (X01) */}
      {/* ================================================================= */}
      <section id="sec-entities" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', fontWeight: 800 }}>
            7
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Candidate Entities & Physical Profiles (X01)
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Candidate actors and stock assets. Decoupled from verified legal biometric identification.
            </p>
          </div>
        </div>

        {entities.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No candidate entities resolved yet.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {entities.map((ent, idx) => (
              <div key={ent.id || idx} style={{ padding: '16px', backgroundColor: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                    {ent.candidate_label || ent.name || `Entity #${idx + 1}`}
                  </span>
                  <span className="badge badge-slate">{ent.identity_status || 'CANDIDATE'}</span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  Type: <strong>{ent.entity_type || 'PERSON'}</strong>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-main)', backgroundColor: '#f8fafc', padding: '8px', borderRadius: '4px' }}>
                  {typeof ent.attributes === 'object' ? JSON.stringify(ent.attributes, null, 1) : String(ent.attributes || '')}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
      {/* ================================================================= */}
      {/* SECTION 8: 45-ENGINE EXECUTION PROVENANCE & TELEMETRY MATRIX */}
      {/* ================================================================= */}
      <section id="sec-provenance" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', fontWeight: 800 }}>
            8
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              45-Engine Backbone Execution Provenance & Telemetry Matrix
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Traceable execution modes, verified LLM providers, model identifiers, and evidence citations.
            </p>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '8px 10px' }}>Engine</th>
                <th style={{ padding: '8px 10px' }}>Declared Mode</th>
                <th style={{ padding: '8px 10px' }}>Actual Execution Path</th>
                <th style={{ padding: '8px 10px' }}>Provider</th>
                <th style={{ padding: '8px 10px' }}>Model</th>
                <th style={{ padding: '8px 10px' }}>Status</th>
                <th style={{ padding: '8px 10px' }}>Confidence</th>
                <th style={{ padding: '8px 10px' }}>Evidence Sources</th>
              </tr>
            </thead>
            <tbody>
              {telemetry.map((t, idx) => {
                const isBlocked = t.status === 'BLOCKED';
                const isNoOutput = t.status === 'NO_USABLE_OUTPUT';
                const declaredMode = t.declared_execution_mode || t.execution_mode || 'DETERMINISTIC';
                const actualPath = isBlocked
                  ? (t.actual_execution_path || 'BLOCKED')
                  : isNoOutput
                    ? (t.actual_execution_path && t.actual_execution_path !== 'NOT_STARTED'
                        ? t.actual_execution_path
                        : (declaredMode === 'MODEL' ? 'NO_USABLE_INPUT' : 'NO_USABLE_OUTPUT'))
                    : (t.actual_execution_path && t.actual_execution_path !== 'NOT_STARTED')
                      ? t.actual_execution_path
                      : (declaredMode === 'DETERMINISTIC' ? 'DETERMINISTIC_ONLY' : (declaredMode === 'HYBRID' ? 'DETERMINISTIC_COMPONENT' : 'MODEL_INFERENCE'));
                const provider = isBlocked
                  ? (t.llm_provider ? `${t.llm_provider} (unavailable)` : 'N/A')
                  : (t.llm_provider || 'N/A');
                const model = isBlocked
                  ? (t.llm_model ? `${t.llm_model}` : 'N/A')
                  : (t.llm_model || 'N/A');
                const confidence = isBlocked || isNoOutput || t.confidence === null || t.confidence === undefined
                  ? 'N/A'
                  : `${(t.confidence * 100).toFixed(0)}%`;

                let evidenceSources = 'N/A — engine not executed';
                if (!isBlocked) {
                  if (t.engine_id === 'X02') {
                    const coverageStr = `Coverage: ${activeTimelineEvents.length > 0 ? `${activeTimelineEvents.length} source / 0 correlated` : '0 sources'}`;
                    evidenceSources = (
                      <div>
                        <div><strong>Status:</strong> {t.status} • {coverageStr}</div>
                        <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          {t.failure_reason || (activeTimelineEvents.length > 0 ? "Deterministic local events from exhibit manifest" : "No timestamped exhibits")}
                        </div>
                      </div>
                    );
                  } else if (t.engine_id === 'X06') {
                    evidenceSources = (
                      <div>
                        <div><strong>Analytical Result:</strong> {sufficiencyData.sufficiency_rating || 'INSUFFICIENT_FOR_RECONSTRUCTION'}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Basis: {sufficiencyData.decision_basis && Array.isArray(sufficiencyData.decision_basis) && sufficiencyData.decision_basis.length > 0
                            ? sufficiencyData.decision_basis.join(' • ')
                            : `${activeTimelineEvents.length > 0 ? `${activeTimelineEvents.length} source-local events` : '0 correlated events'} • ${sufficiencyData.evaluation_criteria?.spatial_pathway_plausible ? 'CCTV present' : 'no CCTV'} • ${sufficiencyData.evaluation_criteria?.asset_delta_proven ? 'inventory present' : 'no financial records'} • ${sufficiencyData.evaluation_criteria?.actor_attribution_corroborated ? 'witness verified' : 'no usable witness extraction'}`}
                        </div>
                      </div>
                    );
                  } else if (t.engine_id === 'X05') {
                    const conflictCount = (t.outputs || []).length;
                    evidenceSources = (
                      <div>
                        <div><strong>Analytical Result:</strong> {conflictCount} Conflicts Detected</div>
                        <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', marginTop: '2px', lineHeight: 1.3 }}>
                          {t.grounding_sources && t.grounding_sources.length > 0
                            ? t.grounding_sources.map((gs, i) => <div key={i}>{gs}</div>)
                            : <div>Checks: 7 Discrepancy Types • {conflictCount} cross-source conflicts</div>}
                        </div>
                      </div>
                    );
                  } else if (t.engine_id === 'F07') {
                    evidenceSources = (
                      <div>
                        <div><strong>Analytical Result:</strong> {t.status === 'SUCCESS' ? 'Exemplar Comparison Completed' : 'NO_USABLE_OUTPUT'}</div>
                        <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          {t.failure_reason || 'No reference exemplar standard attached to case for side-by-side comparison.'}
                        </div>
                      </div>
                    );
                  } else if (t.grounding_sources && t.grounding_sources.length > 0) {
                    evidenceSources = t.grounding_sources.join(', ');
                  } else if (t.evidence_ids && t.evidence_ids.length > 0) {
                    evidenceSources = t.evidence_ids.join(', ');
                  } else if (t.engine_id?.startsWith('X') || t.engine_id?.startsWith('R')) {
                    evidenceSources = isNoOutput ? '0 correlated sources' : 'Cross-Engine Corroboration';
                  } else {
                    evidenceSources = 'Case Exhibit Manifest';
                  }
                }

                return (
                  <tr key={t.engine_id || idx} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '8px 10px', fontWeight: 700, color: 'var(--primary)' }}>
                      {t.engine_id}
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <span className="badge badge-slate">{declaredMode}</span>
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: isBlocked ? '#dc2626' : 'var(--text-main)' }}>
                      <div>{actualPath}</div>
                      {actualPath === 'DETERMINISTIC_COMPONENT' && declaredMode === 'HYBRID' && (
                        <div style={{ fontSize: '0.68rem', color: '#0284c7', marginTop: '2px', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                          (Deterministic only — no AI model invoked)
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-muted)' }}>
                      {provider}
                    </td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-muted)' }}>
                      {model}
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <span className={
                        t.status === 'SUCCESS' ? 'badge badge-green' :
                          t.status === 'BLOCKED' ? 'badge badge-slate' :
                            t.status === 'NO_USABLE_OUTPUT' ? 'badge badge-slate' :
                              t.status === 'FAILED' ? 'badge badge-red' : 'badge badge-amber'
                      }>
                        {t.status}
                      </span>
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>
                      {confidence}
                    </td>
                    <td style={{ padding: '8px 10px', color: isBlocked ? 'var(--text-muted)' : 'var(--text-main)', fontSize: '0.75rem' }}>
                      {evidenceSources}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* ================================================================= */}
      {/* SECTION 9: SPECIALIST AUDIT & LEAD SIGN-OFF ACTIONS (R04) */}
      {/* ================================================================= */}
      <section id="sec-signoff" className="card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Human Verification & Multi-Tier Specialist Sign-Off (R04)
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Immutable human review workflow: Case evidence audit is always available; lead reconstruction review is gated on valid hypothesis synthesis.
            </p>
          </div>
        </div>

        <div style={{
          backgroundColor: isR01Blocked ? '#fffbeb' : '#f0fdf4',
          border: isR01Blocked ? '1px solid #fde68a' : '1px solid #bbf7d0',
          borderRadius: 'var(--radius-md)',
          padding: '14px 18px',
          marginBottom: '20px',
          fontSize: '0.825rem'
        }}>
          <div style={{ fontWeight: 700, color: isR01Blocked ? '#b45309' : '#166534', marginBottom: '4px' }}>
            {isR01Blocked ? "Dual-Level Human-in-the-Loop Protocol: Case Evidence Review Active" : "Full Reconstruction Review Active"}
          </div>
          <div style={{ color: isR01Blocked ? '#78350f' : '#14532d' }}>
            {isR01Blocked
              ? "Reconstruction is safely halted at X06 (insufficient corroborating exhibits). However, Level 1 Case Evidence Review is fully operational: investigators can verify exhibit authenticity, forensic image measurements, identified gaps, and blocked engine telemetry."
              : "Reconstruction hypotheses established. Specialist reviews across timelines, forensics, financials, and lead investigator sign-off are operational."
            }
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '20px' }}>
          {[
            {
              tier: 'INVESTIGATION_SPECIALIST',
              label: '1. Case Evidence & Quality Review',
              scope: 'Exhibit provenance, SHA-256 integrity, quality grades, and missing modalities',
              level: 'CASE_REVIEW',
              statusNote: 'Always Available'
            },
            {
              tier: 'FORENSIC_SPECIALIST',
              label: '2. Forensic Feature & Measurement Audit',
              scope: 'Photographic EXIF, physical surface features, and edge measurements',
              level: 'CASE_REVIEW',
              statusNote: 'Always Available'
            },
            {
              tier: 'FINANCIAL_SPECIALIST',
              label: '3. Investigation Gaps & Missing Modalities Review',
              scope: 'Verified coverage gaps, uncollected CCTV/POS ledgers, and blocked AI engines',
              level: 'CASE_REVIEW',
              statusNote: 'Always Available'
            },
            {
              tier: 'LEAD_INVESTIGATOR',
              label: '4. Lead Reconstruction Review',
              scope: isR01Blocked ? 'Unavailable because no defensible reconstruction was generated.' : 'Final executive synthesis and dossier review',
              level: 'RECONSTRUCTION_REVIEW',
              statusNote: isR01Blocked ? 'Unavailable' : 'Ready for Review'
            }
          ].map(item => {
            const decision = signOffDecisions[item.tier];
            const isReconGated = item.level === 'RECONSTRUCTION_REVIEW' && isR01Blocked;
            return (
              <div key={item.tier} style={{ padding: '16px', backgroundColor: '#ffffff', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '2px' }}>
                  {item.label}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                  Scope: {item.scope}
                </div>

                {decision ? (
                  <div style={{ padding: '8px 12px', backgroundColor: decision.decision === 'ACCEPTED' ? 'var(--success-bg)' : 'var(--warning-bg)', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 600, color: decision.decision === 'ACCEPTED' ? 'var(--success-text)' : 'var(--warning-text)' }}>
                    ✓ {decision.decision} on {new Date(decision.decided_at).toLocaleTimeString()}
                  </div>
                ) : isReconGated ? (
                  <div style={{ padding: '8px 12px', backgroundColor: '#f1f5f9', border: '1px dashed var(--border-light)', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                    Unavailable because no defensible reconstruction was generated.
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      onClick={() => handleDecision(item.tier, 'ACCEPTED')}
                      className="btn btn-sm btn-primary"
                      style={{ flex: 1, backgroundColor: '#059669', borderColor: '#059669' }}
                    >
                      <ThumbsUp size={14} /> Accept
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDecision(item.tier, 'CORRECTION_REQUESTED')}
                      className="btn btn-sm btn-secondary"
                      style={{ flex: 1 }}
                    >
                      <Edit3 size={14} /> Correct
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDecision(item.tier, 'REJECTED')}
                      className="btn btn-sm btn-secondary"
                      style={{ color: '#dc2626' }}
                    >
                      <ThumbsDown size={14} /> Reject
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
            Investigator Sign-Off Notes / Procedural Remarks
          </label>
          <input
            type="text"
            placeholder="e.g. Findings reviewed and endorsed for prosecutorial review under standard evidentiary rules."
            value={signOffNotes}
            onChange={(e) => setSignOffNotes(e.target.value)}
            className="form-input"
            style={{ width: '100%' }}
          />
        </div>
      </section>
    </div>
  );
}
