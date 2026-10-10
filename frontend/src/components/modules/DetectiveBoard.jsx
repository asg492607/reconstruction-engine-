import React, { useState, useEffect, useRef } from 'react';
import {
  Compass,
  FileText,
  Users,
  Clock,
  Database,
  Plus,
  Trash2,
  Move,
  Link2,
  Maximize2,
  Minimize2,
  Filter,
  Sparkles,
  Download,
  AlertTriangle,
  CheckCircle2,
  Eye,
  Shield,
  Layers,
  RefreshCw,
  Search,
  StickyNote
} from 'lucide-react';

export default function DetectiveBoard({
  caseData,
  evidence = [],
  timelineEvents = [],
  entities = [],
  hypotheses = [],
  onNavigate
}) {
  const containerRef = useRef(null);
  const [filterType, setFilterType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [connectingSource, setConnectingSource] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false);
  const [newNoteTitle, setNewNoteTitle] = useState('');
  const [newNoteText, setNewNoteText] = useState('');
  const [newNoteColor, setNewNoteColor] = useState('#fef08a'); // pastel yellow

  // Pins state
  const storageKey = `rre_board_pins_${caseData?.id || 'default'}`;
  const linksKey = `rre_board_links_${caseData?.id || 'default'}`;

  const [pins, setPins] = useState([]);
  const [links, setLinks] = useState([]);
  const [draggedPinId, setDraggedPinId] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // Initialize or load board pins
  useEffect(() => {
    try {
      const savedPins = localStorage.getItem(storageKey);
      const savedLinks = localStorage.getItem(linksKey);
      if (savedPins) {
        setPins(JSON.parse(savedPins));
      } else {
        autoGeneratePins();
      }

      if (savedLinks) {
        setLinks(JSON.parse(savedLinks));
      } else {
        autoGenerateLinks();
      }
    } catch (e) {
      autoGeneratePins();
      autoGenerateLinks();
    }
  }, [caseData?.id, evidence.length, entities.length, timelineEvents.length]);

  // Save changes to localStorage
  const saveState = (updatedPins, updatedLinks) => {
    try {
      if (updatedPins) localStorage.setItem(storageKey, JSON.stringify(updatedPins));
      if (updatedLinks) localStorage.setItem(linksKey, JSON.stringify(updatedLinks));
    } catch (e) {
      console.warn("Failed to save board state:", e);
    }
  };

  const autoGeneratePins = () => {
    const newPins = [];
    let col1Y = 40, col2Y = 40, col3Y = 40, col4Y = 40;

    // Col 1: Evidence (X: 40)
    evidence.slice(0, 8).forEach((item, idx) => {
      newPins.push({
        id: `ev_${item.id || idx}`,
        type: 'EVIDENCE',
        refId: item.id,
        title: item.title || item.original_filename || `Evidence #${idx + 1}`,
        subtitle: item.evidence_type || 'ARTIFACT',
        meta: {
          hash: item.sha256_hash ? `${item.sha256_hash.substring(0, 12)}...` : null,
          dept: item.department,
          ocr: item.metadata_json?.ocr_data
        },
        x: 40,
        y: col1Y
      });
      col1Y += 150;
    });

    // Col 2: Timeline Milestones (X: 380)
    timelineEvents.slice(0, 6).forEach((evt, idx) => {
      newPins.push({
        id: `tl_${evt.id || idx}`,
        type: 'TIMELINE',
        refId: evt.id,
        title: evt.event_time ? new Date(evt.event_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : `Milestone #${idx + 1}`,
        subtitle: evt.description || evt.title || 'Observed activity',
        meta: {
          location: evt.location,
          dept: evt.department
        },
        x: 380,
        y: col2Y
      });
      col2Y += 140;
    });

    // Col 3: Entities / Suspects (X: 720)
    entities.slice(0, 6).forEach((ent, idx) => {
      newPins.push({
        id: `ent_${ent.id || idx}`,
        type: 'ENTITY',
        refId: ent.id,
        title: ent.label || ent.name || `Entity #${idx + 1}`,
        subtitle: ent.entity_type || 'PERSON',
        meta: {
          status: ent.identity_status || ent.status || 'CANDIDATE',
          desc: ent.description
        },
        x: 720,
        y: col3Y
      });
      col3Y += 145;
    });

    // Col 4: Detective Notes & Hypotheses (X: 1060)
    newPins.push({
      id: 'note_initial_lead',
      type: 'NOTE',
      title: 'Primary Detective Theory',
      subtitle: 'Focus on perimeter entry between 02:38 and 02:44 AM. Cross-verify register tape discrepancy with store manager.',
      meta: {
        color: '#fef08a',
        author: 'Lead Detective'
      },
      x: 1060,
      y: 40
    });

    if (evidence.some(e => e.metadata_json?.ocr_data)) {
      newPins.push({
        id: 'note_ocr_audit',
        type: 'NOTE',
        title: 'Forensic OCR Discrepancy',
        subtitle: 'Hand-altered timestamp detected on register receipt tape. Possible insider staging.',
        meta: {
          color: '#fed7aa',
          author: 'Forensic Specialist'
        },
        x: 1060,
        y: 220
      });
    }

    setPins(newPins);
    saveState(newPins, null);
  };

  const autoGenerateLinks = () => {
    const newLinks = [];
    // Automatically link timeline events to entities or evidence if IDs match
    if (evidence.length > 0 && entities.length > 0) {
      newLinks.push({
        id: 'link_1',
        from: `ev_${evidence[0].id || 0}`,
        to: `ent_${entities[0]?.id || 0}`,
        relation: 'CCTV Identification Match',
        type: 'SUSPICIOUS' // red
      });
    }

    if (timelineEvents.length > 0 && evidence.length > 1) {
      newLinks.push({
        id: 'link_2',
        from: `tl_${timelineEvents[0].id || 0}`,
        to: `ev_${evidence[1]?.id || 1}`,
        relation: 'Temporal Anchor Match',
        type: 'CORROBORATED' // blue
      });
    }

    setLinks(newLinks);
    saveState(null, newLinks);
  };

  // Node Dragging Handlers
  const handleMouseDown = (e, pin) => {
    if (e.button !== 0) return; // only left click
    const rect = e.currentTarget.getBoundingClientRect();
    setDraggedPinId(pin.id);
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };

  const handleMouseMove = (e) => {
    if (!draggedPinId || !containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const newX = Math.max(10, Math.min(1400, e.clientX - containerRect.left - dragOffset.x));
    const newY = Math.max(10, Math.min(1200, e.clientY - containerRect.top - dragOffset.y));

    setPins(prev => {
      const next = prev.map(p => p.id === draggedPinId ? { ...p, x: newX, y: newY } : p);
      saveState(next, null);
      return next;
    });
  };

  const handleMouseUp = () => {
    setDraggedPinId(null);
  };

  // Connect Two Pins with Yarn
  const handlePinClick = (pin) => {
    if (connectingSource) {
      if (connectingSource.id === pin.id) {
        setConnectingSource(null);
        return;
      }
      // Create new link
      const newLink = {
        id: `link_${Date.now()}`,
        from: connectingSource.id,
        to: pin.id,
        relation: 'Investigative Link',
        type: 'SUSPICIOUS'
      };
      const updated = [...links, newLink];
      setLinks(updated);
      saveState(null, updated);
      setConnectingSource(null);
    } else {
      setSelectedNode(pin);
    }
  };

  const handleAddNote = () => {
    if (!newNoteTitle.trim()) return;
    const newNote = {
      id: `note_${Date.now()}`,
      type: 'NOTE',
      title: newNoteTitle.trim(),
      subtitle: newNoteText.trim() || 'No additional note body.',
      meta: {
        color: newNoteColor,
        author: 'Investigator'
      },
      x: 1060,
      y: 120 + Math.random() * 200
    };
    const updated = [...pins, newNote];
    setPins(updated);
    saveState(updated, null);
    setNewNoteTitle('');
    setNewNoteText('');
    setIsNoteModalOpen(false);
  };

  const handleDeletePin = (pinId) => {
    const updatedPins = pins.filter(p => p.id !== pinId);
    const updatedLinks = links.filter(l => l.from !== pinId && l.to !== pinId);
    setPins(updatedPins);
    setLinks(updatedLinks);
    saveState(updatedPins, updatedLinks);
    if (selectedNode?.id === pinId) setSelectedNode(null);
  };

  const handleDeleteLink = (linkId) => {
    const updated = links.filter(l => l.id !== linkId);
    setLinks(updated);
    saveState(null, updated);
  };

  // Filter Pins
  const filteredPins = pins.filter(p => {
    if (filterType !== 'ALL' && p.type !== filterType) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        p.title.toLowerCase().includes(q) ||
        p.subtitle.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Top Controls Toolbar */}
      <div className="card" style={{
        padding: '16px 20px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '14px',
        backgroundColor: '#ffffff'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            backgroundColor: '#0f172a',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Compass size={20} color="#38bdf8" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              Detective Case Canvas & Crime Board
              <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>PALANTIR STYLE</span>
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
              Spatial evidence synthesis • Interactive investigative red-yarn correlation • Dynamic clue pinning
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="Filter canvas items..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input"
              style={{ paddingLeft: '30px', paddingRight: '10px', fontSize: '0.8rem', width: '180px' }}
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="form-select"
            style={{ fontSize: '0.8rem', padding: '6px 10px', width: 'auto' }}
          >
            <option value="ALL">All Modalities</option>
            <option value="EVIDENCE">Evidence Exhibits</option>
            <option value="TIMELINE">Timeline Anchors</option>
            <option value="ENTITY">Entities & Suspects</option>
            <option value="NOTE">Detective Notes</option>
          </select>

          <button
            onClick={() => setConnectingSource(connectingSource ? null : pins[0])}
            className={`btn btn-sm ${connectingSource ? 'btn-danger' : 'btn-outline'}`}
            style={{ fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '5px' }}
          >
            <Link2 size={14} />
            {connectingSource ? 'Cancel Linking' : 'Connect Clues'}
          </button>

          <button
            onClick={() => setIsNoteModalOpen(true)}
            className="btn btn-primary btn-sm"
            style={{ fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '5px' }}
          >
            <Plus size={14} />
            Add Sticky Note
          </button>

          <button
            onClick={autoGeneratePins}
            className="btn btn-secondary btn-sm"
            title="Reset to organized forensic columns"
            style={{ fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '5px' }}
          >
            <RefreshCw size={14} />
            Auto-Arrange
          </button>
        </div>
      </div>

      {connectingSource && (
        <div style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: 'var(--radius-md)',
          padding: '10px 16px',
          color: '#1e40af',
          fontSize: '0.825rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Link2 size={16} />
            <span>Select a second clue card on the canvas to attach red correlation yarn to <strong>{connectingSource.title}</strong></span>
          </div>
          <button onClick={() => setConnectingSource(null)} className="btn btn-outline btn-sm" style={{ padding: '2px 8px', fontSize: '0.75rem' }}>
            Cancel
          </button>
        </div>
      )}

      {/* Main Forensic Canvas */}
      <div
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        style={{
          position: 'relative',
          width: '100%',
          height: '740px',
          backgroundColor: '#090d16',
          backgroundImage: `
            radial-gradient(circle, rgba(255, 255, 255, 0.08) 1px, transparent 1px),
            linear-gradient(rgba(15, 23, 42, 0.6) 1px, transparent 1px),
            linear-gradient(90deg, rgba(15, 23, 42, 0.6) 1px, transparent 1px)
          `,
          backgroundSize: '24px 24px, 120px 120px, 120px 120px',
          borderRadius: 'var(--radius-lg)',
          border: '2px solid #1e293b',
          overflow: 'auto',
          boxShadow: 'inset 0 0 40px rgba(0,0,0,0.8)'
        }}
      >
        {/* SVG String / Yarn Layer */}
        <svg
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '1600px',
            height: '1400px',
            pointerEvents: 'none',
            zIndex: 1
          }}
        >
          <defs>
            <filter id="yarnGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {links.map((link) => {
            const fromPin = pins.find(p => p.id === link.from);
            const toPin = pins.find(p => p.id === link.to);
            if (!fromPin || !toPin) return null;

            const startX = fromPin.x + 130;
            const startY = fromPin.y + 60;
            const endX = toPin.x + 130;
            const endY = toPin.y + 60;

            const strokeColor = link.type === 'SUSPICIOUS' ? '#ef4444' : (link.type === 'CORROBORATED' ? '#38bdf8' : '#eab308');

            // Curved quadratic or cubic line for realistic hanging yarn
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2 + 30; // sag

            return (
              <g key={link.id}>
                {/* Shadow */}
                <path
                  d={`M ${startX} ${startY} Q ${midX} ${midY + 6} ${endX} ${endY}`}
                  stroke="rgba(0,0,0,0.5)"
                  strokeWidth="3.5"
                  fill="none"
                />
                {/* Yarn String */}
                <path
                  d={`M ${startX} ${startY} Q ${midX} ${midY} ${endX} ${endY}`}
                  stroke={strokeColor}
                  strokeWidth="2.5"
                  strokeDasharray={link.type === 'SUSPICIOUS' ? 'none' : '6,3'}
                  fill="none"
                  filter="url(#yarnGlow)"
                />
                {/* Pushpin anchors at ends */}
                <circle cx={startX} cy={startY} r="5" fill="#f87171" stroke="#ffffff" strokeWidth="1.5" />
                <circle cx={endX} cy={endY} r="5" fill="#f87171" stroke="#ffffff" strokeWidth="1.5" />

                {/* Link Label Tag */}
                <foreignObject x={midX - 70} y={midY - 14} width="140" height="28" style={{ pointerEvents: 'auto' }}>
                  <div
                    onClick={() => handleDeleteLink(link.id)}
                    title="Click to remove yarn string"
                    style={{
                      backgroundColor: 'rgba(15, 23, 42, 0.85)',
                      color: strokeColor,
                      border: `1px solid ${strokeColor}`,
                      borderRadius: '12px',
                      padding: '2px 8px',
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      textAlign: 'center',
                      cursor: 'pointer',
                      backdropFilter: 'blur(4px)',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    ✕ {link.relation}
                  </div>
                </foreignObject>
              </g>
            );
          })}
        </svg>

        {/* Pinned Cards */}
        {filteredPins.map((pin) => {
          const isSelected = selectedNode?.id === pin.id;
          const isConnectingFrom = connectingSource?.id === pin.id;

          if (pin.type === 'NOTE') {
            return (
              <div
                key={pin.id}
                onMouseDown={(e) => handleMouseDown(e, pin)}
                onClick={() => handlePinClick(pin)}
                style={{
                  position: 'absolute',
                  left: `${pin.x}px`,
                  top: `${pin.y}px`,
                  width: '240px',
                  backgroundColor: pin.meta?.color || '#fef08a',
                  color: '#1c1917',
                  padding: '16px',
                  borderRadius: '3px',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.5)',
                  cursor: draggedPinId === pin.id ? 'grabbing' : 'grab',
                  zIndex: isSelected ? 20 : 10,
                  transform: 'rotate(-1.5deg)',
                  border: isConnectingFrom ? '3px solid #38bdf8' : 'none'
                }}
              >
                {/* Brass pin top */}
                <div style={{
                  position: 'absolute',
                  top: '-8px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '14px',
                  height: '14px',
                  borderRadius: '50%',
                  backgroundColor: '#dc2626',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.4)',
                  border: '2px solid #ffffff'
                }} />

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div style={{ fontWeight: 800, fontSize: '0.875rem' }}>{pin.title}</div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeletePin(pin.id); }}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#78716c', padding: 0 }}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
                <div style={{ fontSize: '0.78rem', lineHeight: 1.4, whiteSpace: 'pre-wrap', fontFamily: 'var(--font-sans)' }}>
                  {pin.subtitle}
                </div>
                <div style={{ fontSize: '0.65rem', color: '#78716c', marginTop: '10px', textAlign: 'right', fontWeight: 600 }}>
                  — {pin.meta?.author || 'Investigator'}
                </div>
              </div>
            );
          }

          // Evidence, Timeline, Entity Cards
          return (
            <div
              key={pin.id}
              onMouseDown={(e) => handleMouseDown(e, pin)}
              onClick={() => handlePinClick(pin)}
              style={{
                position: 'absolute',
                left: `${pin.x}px`,
                top: `${pin.y}px`,
                width: '260px',
                backgroundColor: '#1e293b',
                color: '#f8fafc',
                borderRadius: '8px',
                border: isConnectingFrom ? '2px solid #38bdf8' : (isSelected ? '2px solid #ef4444' : '1px solid #334155'),
                padding: '14px',
                boxShadow: isSelected ? '0 0 16px rgba(239, 68, 68, 0.4)' : '0 6px 18px rgba(0,0,0,0.6)',
                cursor: draggedPinId === pin.id ? 'grabbing' : 'grab',
                zIndex: isSelected ? 20 : 10,
                transition: 'border 0.2s, box-shadow 0.2s'
              }}
            >
              {/* Pushpin indicator */}
              <div style={{
                position: 'absolute',
                top: '-7px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: pin.type === 'EVIDENCE' ? '#38bdf8' : (pin.type === 'ENTITY' ? '#a855f7' : '#10b981'),
                border: '2px solid #ffffff',
                boxShadow: '0 2px 4px rgba(0,0,0,0.5)'
              }} />

              {/* Card Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span className="badge" style={{
                  fontSize: '0.65rem',
                  padding: '2px 6px',
                  backgroundColor: pin.type === 'EVIDENCE' ? 'rgba(56, 189, 248, 0.2)' : (pin.type === 'ENTITY' ? 'rgba(168, 85, 247, 0.2)' : 'rgba(16, 185, 129, 0.2)'),
                  color: pin.type === 'EVIDENCE' ? '#38bdf8' : (pin.type === 'ENTITY' ? '#c084fc' : '#34d399'),
                  border: '1px solid rgba(255,255,255,0.1)'
                }}>
                  {pin.type}
                </span>

                <button
                  onClick={(e) => { e.stopPropagation(); handleDeletePin(pin.id); }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
                >
                  <Trash2 size={13} />
                </button>
              </div>

              {/* Title & Subtitle */}
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#ffffff', marginBottom: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {pin.title}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.3, marginBottom: '8px' }}>
                {pin.subtitle}
              </div>

              {/* Metadata Badges */}
              {pin.meta?.ocr && (
                <div style={{
                  backgroundColor: 'rgba(126, 34, 206, 0.25)',
                  border: '1px solid #9333ea',
                  borderRadius: '4px',
                  padding: '3px 6px',
                  fontSize: '0.68rem',
                  color: '#e9d5ff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginBottom: '6px'
                }}>
                  <Sparkles size={11} color="#c084fc" />
                  <span>OCR: {pin.meta.ocr.total_amount ? `${pin.meta.ocr.total_amount}` : 'Transcribed'}</span>
                </div>
              )}

              {pin.meta?.hash && (
                <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>
                  SHA256: {pin.meta.hash}
                </div>
              )}

              {pin.meta?.location && (
                <div style={{ fontSize: '0.7rem', color: '#38bdf8', marginTop: '4px' }}>
                  📍 {pin.meta.location}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Selected Node Inspector Drawer / Bar */}
      {selectedNode && (
        <div className="card" style={{
          padding: '16px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#ffffff',
          borderLeft: '4px solid var(--primary)'
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>
              INSPECTING PINNED NODE [{selectedNode.type}]
            </div>
            <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text-main)' }}>
              {selectedNode.title}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {selectedNode.subtitle}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setConnectingSource(selectedNode)}
              className="btn btn-outline btn-sm"
              style={{ fontSize: '0.75rem' }}
            >
              <Link2 size={13} />
              Connect to Another Pin
            </button>
            <button
              onClick={() => setSelectedNode(null)}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '0.75rem' }}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Add Detective Note Modal */}
      {isNoteModalOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.5)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '16px'
        }}>
          <div className="card animate-fade-in" style={{ maxWidth: '440px', width: '100%', padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <StickyNote size={18} color="var(--primary)" />
              Pin New Detective Note to Board
            </h3>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>
                Note Title / Subject
              </label>
              <input
                type="text"
                placeholder="e.g. Alibi Discrepancy, Witness Conflict"
                value={newNoteTitle}
                onChange={(e) => setNewNoteTitle(e.target.value)}
                className="form-input"
              />
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>
                Investigative Narrative / Clue Details
              </label>
              <textarea
                rows={3}
                placeholder="Detail observations, questions, or follow-up directions..."
                value={newNoteText}
                onChange={(e) => setNewNoteText(e.target.value)}
                className="form-input"
              />
            </div>

            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                Sticky Note Color
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[
                  { color: '#fef08a', name: 'Yellow' },
                  { color: '#bbf7d0', name: 'Green' },
                  { color: '#fed7aa', name: 'Amber' },
                  { color: '#fbcfe8', name: 'Rose' },
                  { color: '#bae6fd', name: 'Blue' }
                ].map((c) => (
                  <button
                    key={c.color}
                    type="button"
                    onClick={() => setNewNoteColor(c.color)}
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      backgroundColor: c.color,
                      border: newNoteColor === c.color ? '2px solid #000' : '1px solid rgba(0,0,0,0.2)',
                      cursor: 'pointer'
                    }}
                  />
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button onClick={() => setIsNoteModalOpen(false)} className="btn btn-secondary btn-sm">
                Cancel
              </button>
              <button onClick={handleAddNote} className="btn btn-primary btn-sm">
                Pin to Board
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
