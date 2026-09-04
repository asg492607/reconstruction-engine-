import React, { useState } from 'react';
import { 
  Clock, 
  MapPin, 
  Shield, 
  Layers, 
  CheckCircle, 
  Filter,
  Calendar,
  AlertCircle
} from 'lucide-react';

export default function CorrelatedTimeline({ timelineEvents = [] }) {
  const [filterDept, setFilterDept] = useState('ALL');

  const filteredEvents = timelineEvents.filter(ev => {
    if (filterDept === 'ALL') return true;
    return ev.department === filterDept || ev.source_department === filterDept;
  });

  const getDeptColor = (dept) => {
    switch(dept) {
      case 'INVESTIGATION': return 'badge-blue';
      case 'FORENSICS': return 'badge-purple';
      case 'FINANCIAL': return 'badge-amber';
      case 'CYBER': return 'badge-green';
      default: return 'badge-slate';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Controls */}
      <div className="card" style={{ padding: '18px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={20} color="var(--primary)" />
            Multi-Source Correlated Timeline
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            Synchronized chronological reality reconstruction across physical, visual, cyber, and financial event streams.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={15} color="var(--text-muted)" />
          <select
            aria-label="Filter timeline events by department"
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
            className="form-select"
            style={{ padding: '7px 12px', fontSize: '0.825rem', width: 'auto' }}
          >
            <option value="ALL">All Event Streams</option>
            <option value="INVESTIGATION">Investigation</option>
            <option value="FORENSICS">Forensics & CCTV</option>
            <option value="CYBER">Cyber & Keycard Logs</option>
            <option value="FINANCIAL">Financial Ledgers</option>
          </select>
        </div>
      </div>

      {/* Timeline Stream */}
      <div className="card" style={{ padding: '28px' }}>
        {filteredEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
            <Clock size={36} color="var(--text-light)" style={{ margin: '0 auto 12px auto' }} />
            <div>No correlated timeline events recorded yet.</div>
          </div>
        ) : (
          <div style={{ position: 'relative', paddingLeft: '28px', borderLeft: '2px solid var(--primary-light)' }}>
            {filteredEvents.map((event, idx) => {
              const conf = event.confidence_score ? Math.round(event.confidence_score * 100) : 85;
              const formattedTime = event.event_time 
                ? new Date(event.event_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                : `02:${40 + idx * 4}:00 AM`;

              return (
                <div key={event.id || idx} style={{ position: 'relative', marginBottom: '32px' }}>
                  {/* Timeline Dot */}
                  <div style={{
                    position: 'absolute',
                    left: '-35px',
                    top: '0',
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--primary)',
                    boxShadow: '0 0 0 4px #ffffff, 0 0 0 6px var(--primary-light)'
                  }} />

                  <div style={{
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    backgroundColor: '#ffffff',
                    boxShadow: 'var(--shadow-sm)'
                  }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
                          {formattedTime}
                        </span>
                        <span className={`badge ${getDeptColor(event.department || event.source_department)}`}>
                          {event.department || event.source_department || 'EVENT'}
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {event.location && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            <MapPin size={13} color="var(--primary)" />
                            {event.location}
                          </div>
                        )}
                        <span className="badge badge-blue">
                          Confidence: {conf}%
                        </span>
                      </div>
                    </div>

                    <p style={{ fontSize: '0.875rem', color: 'var(--text-main)', lineHeight: 1.5, marginBottom: '6px' }}>
                      {event.description || event.title}
                    </p>

                    {event.source_evidence_title && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>Source:</span>
                        <span style={{ fontWeight: 600, color: 'var(--primary)' }}>{event.source_evidence_title}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
