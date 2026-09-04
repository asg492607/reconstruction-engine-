import React, { useState } from 'react';
import { 
  Users, 
  Car, 
  Package, 
  MapPin, 
  CheckCircle2, 
  HelpCircle, 
  Check, 
  Search,
  Filter
} from 'lucide-react';
import { api } from '../../api';

export default function EntityNetwork({ caseId, entities = [], onRefresh }) {
  const [filterType, setFilterType] = useState('ALL');
  const [confirmingId, setConfirmingId] = useState(null);

  const handleConfirm = async (entityId) => {
    setConfirmingId(entityId);
    try {
      await api.entities.confirm(caseId, entityId);
      onRefresh();
    } catch (err) {
      alert("Failed to confirm entity: " + err.message);
    } finally {
      setConfirmingId(null);
    }
  };

  const filteredEntities = entities.filter(ent => {
    if (filterType === 'ALL') return true;
    return ent.entity_type === filterType;
  });

  const getEntityIcon = (type) => {
    switch(type) {
      case 'PERSON': return <Users size={18} color="var(--primary)" />;
      case 'VEHICLE': return <Car size={18} color="#7c3aed" />;
      case 'PROPERTY': return <Package size={18} color="#d97706" />;
      case 'LOCATION': return <MapPin size={18} color="#059669" />;
      default: return <Users size={18} color="var(--text-muted)" />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div className="card" style={{ padding: '18px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={20} color="var(--primary)" />
            Extracted Entity Ground-Truth Network
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            Distinguishes unconfirmed candidates extracted by AI from confirmed ground-truth case entities.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={15} color="var(--text-muted)" />
          <select
            aria-label="Filter entities by type"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="form-select"
            style={{ padding: '7px 12px', fontSize: '0.825rem', width: 'auto' }}
          >
            <option value="ALL">All Entity Types</option>
            <option value="PERSON">Persons & Suspects</option>
            <option value="VEHICLE">Vehicles</option>
            <option value="PROPERTY">Stolen Property</option>
            <option value="LOCATION">Locations</option>
          </select>
        </div>
      </div>

      {/* Grid of Entity Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px'
      }}>
        {filteredEntities.length === 0 ? (
          <div className="card" style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No entities matching filter.
          </div>
        ) : (
          filteredEntities.map((entity) => {
            const isConfirmed = entity.status === 'CONFIRMED';

            return (
              <div 
                key={entity.id}
                className="card"
                style={{
                  padding: '18px',
                  borderColor: isConfirmed ? 'var(--success-border)' : 'var(--border-light)',
                  borderLeft: isConfirmed ? '4px solid #059669' : '4px solid #d97706'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getEntityIcon(entity.entity_type)}
                    <div>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)' }}>
                        {entity.name}
                      </h4>
                      <span className="badge badge-slate" style={{ fontSize: '0.68rem', marginTop: '2px' }}>
                        {entity.entity_type}
                      </span>
                    </div>
                  </div>

                  {isConfirmed ? (
                    <span className="badge badge-green">
                      <CheckCircle2 size={12} />
                      CONFIRMED
                    </span>
                  ) : (
                    <span className="badge badge-amber">
                      <HelpCircle size={12} />
                      CANDIDATE
                    </span>
                  )}
                </div>

                {/* Attributes / Metadata */}
                <div style={{
                  fontSize: '0.78rem',
                  color: 'var(--text-muted)',
                  backgroundColor: 'var(--bg-app)',
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '14px'
                }}>
                  {entity.attributes ? (
                    typeof entity.attributes === 'object' ? (
                      Object.entries(entity.attributes).map(([k, v]) => (
                        <div key={k} style={{ marginBottom: '2px' }}>
                          <strong>{k}:</strong> {String(v)}
                        </div>
                      ))
                    ) : (
                      String(entity.attributes)
                    )
                  ) : (
                    'Standard case entity'
                  )}
                </div>

                {/* Confirm Action */}
                {!isConfirmed && (
                  <button
                    onClick={() => handleConfirm(entity.id)}
                    disabled={confirmingId === entity.id}
                    className="btn btn-primary btn-sm"
                    style={{ width: '100%' }}
                  >
                    <Check size={14} />
                    {confirmingId === entity.id ? 'Confirming...' : 'Confirm Ground Truth'}
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
