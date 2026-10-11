import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '260px',
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#fff',
          borderRadius: '12px',
          border: '1px solid #fed7aa',
          margin: '24px',
          textAlign: 'center',
          boxShadow: '0 4px 12px rgba(15, 23, 42, 0.05)'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: '#fff7ed',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px'
          }}>
            <AlertTriangle size={24} color="#ea580c" />
          </div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', marginBottom: '8px' }}>
            Transient Component Error Detected
          </h2>
          <p style={{ fontSize: '0.825rem', color: '#64748b', maxWidth: '440px', marginBottom: '18px', lineHeight: 1.5 }}>
            {this.state.error?.message || "An unexpected error occurred while rendering this module."}
          </p>
          <button
            onClick={this.handleReload}
            className="btn btn-primary btn-sm"
            style={{ fontWeight: 700 }}
          >
            <RefreshCw size={14} />
            Reload Interface
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
