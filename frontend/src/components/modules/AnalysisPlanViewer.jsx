import React, { useState, useEffect } from 'react';
import { 
  Play, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Layers, 
  Cpu, 
  ShieldAlert, 
  RefreshCw,
  Search,
  ChevronRight,
  Database,
  ArrowRight
} from 'lucide-react';
import { api } from '../../api';

const ENGINE_GROUPS = [
  { id: 'EVIDENCE', title: 'Evidence Foundation (E01–E07)', prefix: 'E', color: '#0ea5e9' },
  { id: 'INVESTIGATION', title: 'Investigation AI (I01–I12)', prefix: 'I', color: '#2563eb' },
  { id: 'FORENSIC', title: 'Forensic AI (F01–F09)', prefix: 'F', color: '#7c3aed' },
  { id: 'FINANCIAL', title: 'Financial AI (FI01–FI07)', prefix: 'FI', color: '#d97706' },
  { id: 'INTELLIGENCE', title: 'Cross-Department Intelligence (X01–X06)', prefix: 'X', color: '#059669' },
  { id: 'RECONSTRUCTION', title: 'Reconstruction & Human Control (R01–R04)', prefix: 'R', color: '#dc2626' }
];

export default function AnalysisPlanViewer({ activeCase, onAnalysisComplete }) {
  const [plan, setPlan] = useState(null);
  const [telemetry, setTelemetry] = useState([]);
  const [registeredEngines, setRegisteredEngines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState('ALL');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (activeCase?.id) {
      loadPlanAndTelemetry(activeCase.id);
    }
  }, [activeCase?.id]);

  const loadPlanAndTelemetry = async (caseId) => {
    setLoading(true);
    setError(null);
    try {
      const [planData, teleData, engineData] = await Promise.allSettled([
        api.cases.getAnalysisPlan(caseId),
        api.cases.getTelemetry(caseId),
        api.engines.list()
      ]);
      if (planData.status === 'fulfilled') setPlan(planData.value);
      if (teleData.status === 'fulfilled') setTelemetry(teleData.value || []);
      if (engineData.status === 'fulfilled') setRegisteredEngines(engineData.value || []);
    } catch (err) {
      setError(err.message || 'Failed to load analysis plan');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!activeCase?.id) return;
    setRunning(true);
    setError(null);
    try {
      await api.cases.runAnalysis(activeCase.id);
      await loadPlanAndTelemetry(activeCase.id);
      if (onAnalysisComplete) {
        onAnalysisComplete();
      }
    } catch (err) {
      setError(err.message || 'Failed to execute analysis plan');
    } finally {
      setRunning(false);
    }
  };

  if (!activeCase) {
    return (
      <div className="empty-state">
        <Cpu size={48} color="var(--text-muted)" />
        <div style={{ fontWeight: 700, marginTop: '12px' }}>No Active Case Selected</div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Select or create an investigation case to view the 45-Engine Backbone.
        </p>
      </div>
    );
  }

  const allItems = plan?.all_items || [];
  const requiredCount = plan?.required_engines?.length || 0;
  const optionalCount = plan?.optional_engines?.length || 0;
  const unavailCount = plan?.unavailable_engines?.length || 0;

  // Map telemetry by engine_id
  const telemetryByEngine = {};
  telemetry.forEach(t => {
    telemetryByEngine[t.engine_id] = t;
  });

  const filteredItems = allItems.filter(item => {
    if (selectedGroup === 'ALL') return true;
    if (selectedGroup === 'EVIDENCE') return item.engine_id.startsWith('E0');
    if (selectedGroup === 'INVESTIGATION') return item.engine_id.startsWith('I');
    if (selectedGroup === 'FORENSIC') return item.engine_id.startsWith('F') && !item.engine_id.startsWith('FI');
    if (selectedGroup === 'FINANCIAL') return item.engine_id.startsWith('FI');
    if (selectedGroup === 'INTELLIGENCE') return item.engine_id.startsWith('X');
    if (selectedGroup === 'RECONSTRUCTION') return item.engine_id.startsWith('R');
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        borderRadius: '16px',
        padding: '24px',
        color: '#ffffff',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '20px',
        boxShadow: '0 10px 25px -5px rgba(15, 23, 42, 0.2)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <span style={{
              backgroundColor: 'rgba(59, 130, 246, 0.25)',
              border: '1px solid rgba(59, 130, 246, 0.5)',
              padding: '2px 10px',
              borderRadius: '20px',
              fontSize: '0.75rem',
              fontWeight: 700,
              color: '#93c5fd'
            }}>
              {activeCase.specific_offense || activeCase.case_type || 'THEFT / ROBBERY'}
            </span>
            <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>
              Case #{activeCase.case_number}
            </span>
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: '0 0 6px 0', letterSpacing: '-0.02em' }}>
            45-Engine Backbone: Dynamic Analysis Plan
          </h2>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#cbd5e1', maxWidth: '640px', lineHeight: 1.4 }}>
            Evidence exhibits are dynamically analyzed by a Kahn-topological DAG. Required engines are activated based on evidence modality; missing data propagates clean unassessable states without hallucinations.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => loadPlanAndTelemetry(activeCase.id)}
            disabled={loading}
            style={{
              padding: '10px 14px',
              borderRadius: '10px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#ffffff',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
            Refresh
          </button>

          <button
            onClick={handleRunAnalysis}
            disabled={running || allItems.length === 0}
            style={{
              padding: '10px 22px',
              borderRadius: '10px',
              backgroundColor: '#2563eb',
              border: 'none',
              color: '#ffffff',
              fontSize: '0.9rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(37, 99, 235, 0.4)'
            }}
          >
            <Play size={16} />
            {running ? 'Executing DAG Sequence...' : 'Execute Analysis Plan'}
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '14px'
      }}>
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid var(--border-light)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            backgroundColor: '#eff6ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#2563eb'
          }}>
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>{requiredCount}</div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>REQUIRED ENGINES</div>
          </div>
        </div>

        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid var(--border-light)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            backgroundColor: '#fefce8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ca8a04'
          }}>
            <Clock size={22} />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>{optionalCount}</div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>OPTIONAL ENGINES</div>
          </div>
        </div>

        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid var(--border-light)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            backgroundColor: '#f1f5f9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b'
          }}>
            <AlertCircle size={22} />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>{unavailCount}</div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>UNAVAILABLE (NO EXHIBIT)</div>
          </div>
        </div>

        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid var(--border-light)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            backgroundColor: '#f0fdf4',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#16a34a'
          }}>
            <Cpu size={22} />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
              {telemetry.length} / 45
            </div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>EXECUTED IN LAST RUN</div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        overflowX: 'auto',
        paddingBottom: '4px'
      }}>
        <button
          onClick={() => setSelectedGroup('ALL')}
          style={{
            padding: '7px 14px',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.8rem',
            fontWeight: 700,
            backgroundColor: selectedGroup === 'ALL' ? 'var(--text-main)' : 'var(--bg-subtle)',
            color: selectedGroup === 'ALL' ? '#ffffff' : 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          All 45 Engines
        </button>
        {ENGINE_GROUPS.map(g => (
          <button
            key={g.id}
            onClick={() => setSelectedGroup(g.id)}
            style={{
              padding: '7px 14px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 700,
              backgroundColor: selectedGroup === g.id ? g.color : 'var(--bg-subtle)',
              color: selectedGroup === g.id ? '#ffffff' : 'var(--text-muted)',
              cursor: 'pointer',
              whiteSpace: 'nowrap'
            }}
          >
            {g.title}
          </button>
        ))}
      </div>

      {/* Engine Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '14px'
      }}>
        {filteredItems.map(item => {
          const tele = telemetryByEngine[item.engine_id];
          const isRequired = item.status === 'REQUIRED';
          const isOptional = item.status === 'OPTIONAL';
          const isUnavail = item.status === 'UNAVAILABLE';

          return (
            <div
              key={item.engine_id}
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                padding: '16px',
                border: '1px solid var(--border-light)',
                borderLeft: `4px solid ${
                  tele?.status === 'SUCCESS' ? '#16a34a' :
                  isRequired ? '#2563eb' :
                  isOptional ? '#ca8a04' : '#94a3b8'
                }`,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '10px'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{
                    fontWeight: 800,
                    fontSize: '0.85rem',
                    color: '#0f172a',
                    backgroundColor: 'var(--bg-subtle)',
                    padding: '2px 8px',
                    borderRadius: '6px'
                  }}>
                    {item.engine_id}
                  </span>

                  <span style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '12px',
                    backgroundColor: isRequired ? '#eff6ff' : isOptional ? '#fefce8' : '#f1f5f9',
                    color: isRequired ? '#1d4ed8' : isOptional ? '#a16207' : '#64748b'
                  }}>
                    {item.status}
                  </span>
                </div>

                <div style={{ fontWeight: 700, fontSize: '0.925rem', color: 'var(--text-main)', marginBottom: '4px' }}>
                  {item.engine_name}
                </div>
                <div style={{ fontSize: '0.785rem', color: 'var(--text-muted)', lineHeight: 1.35 }}>
                  {item.reason}
                </div>
              </div>

              {/* Execution Status / Telemetry */}
              {tele ? (
                <div style={{
                  padding: '8px 10px',
                  borderRadius: '8px',
                  backgroundColor: tele.status === 'SUCCESS' ? '#f0fdf4' : '#fffbeb',
                  border: `1px solid ${tele.status === 'SUCCESS' ? '#bbf7d0' : '#fef3c7'}`,
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={13} color="#16a34a" />
                    <span style={{ fontWeight: 700, color: '#166534' }}>{tele.status}</span>
                  </div>
                  <span style={{ color: '#64748b', fontWeight: 600 }}>
                    {tele.outputs?.length || 0} findings · {Math.round(tele.confidence * 100)}% conf
                  </span>
                </div>
              ) : (
                item.dependencies?.length > 0 && (
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>Prerequisites:</span>
                    <span style={{ fontWeight: 600 }}>{item.dependencies.join(', ')}</span>
                  </div>
                )
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
