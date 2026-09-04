import React, { useState, useRef, useEffect } from 'react';
import { 
  Cpu, 
  Send, 
  ShieldAlert, 
  Sparkles, 
  FileText, 
  CheckCircle2, 
  AlertCircle,
  HelpCircle,
  Clock
} from 'lucide-react';
import { api } from '../../api';

export default function CopilotChat({ caseId }) {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: "Hello, Detective. I am your RRE Investigation Copilot powered by Google Gemini 3.6 Flash. I can synthesize physical evidence, cross-reference CCTV observations, or analyze timeline discrepancies. How may I assist your inquiry today?",
      mode: 'EVIDENCE_ONLY',
      citations: []
    }
  ]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('EVIDENCE_ONLY'); // 'EVIDENCE_ONLY' | 'REASONING_MODE'
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    setMessages(prev => [...prev, { sender: 'user', text: userText }]);
    setLoading(true);

    try {
      const res = await api.copilot.ask(caseId, userText, mode);
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: res.answer || res.response || "Analysis complete.",
        mode: res.mode || mode,
        citations: res.citations || res.sources || []
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: `Error processing inquiry: ${err.message}. Please verify backend connection.`,
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: 'calc(100vh - 180px)' }}>
      {/* Safeguard Notice */}
      <div style={{
        backgroundColor: 'var(--bg-accent-light)',
        border: '1px solid var(--primary-border)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        fontSize: '0.8rem',
        color: 'var(--text-main)'
      }}>
        <ShieldAlert size={18} color="var(--primary)" style={{ flexShrink: 0 }} />
        <span>
          <strong>Evidentiary Safeguard:</strong> This AI copilot is strictly barred from asserting criminal culpability or guilt. All conclusions require independent detective verification.
        </span>
      </div>

      {/* Main Chat Box */}
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Chat Header with Mode Selector */}
        <div style={{
          padding: '14px 20px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#ffffff'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} color="var(--primary)" />
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Investigation Copilot</span>
            <span className="badge badge-purple">Gemini 3.6 Flash</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              type="button"
              onClick={() => setMode('EVIDENCE_ONLY')}
              style={{
                padding: '5px 10px',
                fontSize: '0.75rem',
                fontWeight: 600,
                borderRadius: 'var(--radius-sm)',
                border: '1px solid',
                cursor: 'pointer',
                backgroundColor: mode === 'EVIDENCE_ONLY' ? 'var(--info-bg)' : '#ffffff',
                color: mode === 'EVIDENCE_ONLY' ? 'var(--primary)' : 'var(--text-muted)',
                borderColor: mode === 'EVIDENCE_ONLY' ? 'var(--primary-border)' : 'var(--border-light)'
              }}
            >
              Strict Evidence Mode
            </button>
            <button
              type="button"
              onClick={() => setMode('REASONING_MODE')}
              style={{
                padding: '5px 10px',
                fontSize: '0.75rem',
                fontWeight: 600,
                borderRadius: 'var(--radius-sm)',
                border: '1px solid',
                cursor: 'pointer',
                backgroundColor: mode === 'REASONING_MODE' ? 'var(--purple-bg)' : '#ffffff',
                color: mode === 'REASONING_MODE' ? 'var(--purple-text)' : 'var(--text-muted)',
                borderColor: mode === 'REASONING_MODE' ? 'var(--purple-border)' : 'var(--border-light)'
              }}
            >
              Exploratory Reasoning Mode
            </button>
          </div>
        </div>

        {/* Messages List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((msg, idx) => {
            const isUser = msg.sender === 'user';

            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start'
                }}
              >
                <div style={{
                  maxWidth: '78%',
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-lg)',
                  backgroundColor: isUser ? 'var(--primary)' : 'var(--bg-app)',
                  color: isUser ? '#ffffff' : 'var(--text-main)',
                  border: isUser ? 'none' : '1px solid var(--border-light)',
                  boxShadow: 'var(--shadow-sm)',
                  fontSize: '0.875rem',
                  lineHeight: 1.6
                }}>
                  {!isUser && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                      <span className="badge badge-slate" style={{ fontSize: '0.65rem' }}>
                        {msg.mode || 'ANALYSIS'}
                      </span>
                    </div>
                  )}

                  <div style={{ whiteSpace: 'pre-wrap' }}>
                    {msg.text}
                  </div>

                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(0,0,0,0.06)', fontSize: '0.75rem' }}>
                      <strong style={{ color: 'var(--primary)' }}>Citations:</strong>
                      <ul style={{ paddingLeft: '16px', marginTop: '4px' }}>
                        {msg.citations.map((c, cIdx) => (
                          <li key={cIdx}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                padding: '12px 18px',
                borderRadius: 'var(--radius-lg)',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-light)',
                fontSize: '0.85rem',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <Sparkles size={16} color="var(--primary)" />
                Synthesizing evidentiary response with Gemini 3.6 Flash...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} style={{
          padding: '14px 20px',
          borderTop: '1px solid var(--border-light)',
          display: 'flex',
          gap: '10px',
          backgroundColor: '#ffffff'
        }}>
          <input
            type="text"
            placeholder="Ask about physical evidence, timeline conflicts, or vehicle sightings..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="form-input"
            style={{ flex: 1 }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn btn-primary"
            style={{ padding: '0 18px' }}
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
