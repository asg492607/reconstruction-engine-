import React from 'react';
import { 
  DollarSign, 
  Package, 
  TrendingDown, 
  FileSpreadsheet, 
  AlertOctagon, 
  CheckCircle,
  Upload
} from 'lucide-react';

export default function FinancialDashboard({ evidence = [], onNavigate }) {
  const financialEvidence = evidence.filter(e => 
    e.source_type === 'FINANCIAL_RECORD' || 
    e.department === 'FINANCIAL'
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Banner */}
      <div className="card" style={{
        padding: '24px',
        background: 'linear-gradient(135deg, #fffbeb 0%, #ffffff 100%)',
        borderColor: 'var(--warning-border)',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="badge badge-amber">Financial Crimes & Loss Audit</span>
            <span className="badge badge-slate">Inventory Reconciliation</span>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
            Theft Loss & Discrepancy Reconciliation
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Auditor: Claire Sterling • Department: Financial Crimes Division
          </p>
        </div>

        <button 
          onClick={() => onNavigate('evidence')} 
          className="btn btn-primary"
          style={{ backgroundColor: '#d97706', borderColor: '#d97706' }}
        >
          <Upload size={16} />
          Ingest Audit Ledger
        </button>
      </div>

      {/* Financial Summary KPIs */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px'
      }}>
        <div className="card" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Total Verified Loss Delta
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#dc2626' }}>
            $4,200.00
          </div>
          <div style={{ fontSize: '0.75rem', color: '#dc2626', fontWeight: 600, marginTop: '4px' }}>
            3 Units Apple iPhone 16 Pro Max
          </div>
        </div>

        <div className="card" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Serial / IMEI Numbers Extracted
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)' }}>
            3 IMEIs
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--success-text)', fontWeight: 600, marginTop: '4px' }}>
            Matched against authorized registry dataset
          </div>
        </div>

        <div className="card" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Secondary Market Flag
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#d97706' }}>
            1 Flag
          </div>
          <div style={{ fontSize: '0.75rem', color: '#d97706', marginTop: '4px' }}>
            Candidate listing match in supplied data
          </div>
        </div>
      </div>

      {/* Discrepancy Context Banner */}
      <div style={{
        padding: '12px 16px',
        backgroundColor: 'var(--bg-accent-light)',
        border: '1px solid var(--primary-border)',
        borderRadius: 'var(--radius-md)',
        fontSize: '0.8rem',
        color: 'var(--text-main)'
      }}>
        <strong>Investigative Context:</strong> Inventory discrepancy and the absence of a point-of-sale transaction constitute corroborating observations; they are evaluated alongside physical and visual evidence rather than assumed as autonomous proof of theft.
      </div>

      {/* Stolen Inventory Table */}
      <div className="card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Package size={18} color="#d97706" />
          Theft Inventory Delta Ledger
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 12px' }}>Item Description</th>
                <th style={{ padding: '10px 12px' }}>Serial / IMEI</th>
                <th style={{ padding: '10px 12px' }}>Qty Missing</th>
                <th style={{ padding: '10px 12px' }}>Unit Value</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '12px', fontWeight: 600 }}>Apple iPhone 16 Pro Max 256GB Space Black</td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>IMEI-990281-01</td>
                <td style={{ padding: '12px' }}>1</td>
                <td style={{ padding: '12px' }}>$1,400.00</td>
                <td style={{ padding: '12px' }}><span className="badge badge-red">STOLEN</span></td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '12px', fontWeight: 600 }}>Apple iPhone 16 Pro Max 256GB Desert Titanium</td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>IMEI-990281-02</td>
                <td style={{ padding: '12px' }}>1</td>
                <td style={{ padding: '12px' }}>$1,400.00</td>
                <td style={{ padding: '12px' }}><span className="badge badge-red">STOLEN</span></td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '12px', fontWeight: 600 }}>Apple iPhone 16 Pro Max 256GB Natural Titanium</td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>IMEI-990281-03</td>
                <td style={{ padding: '12px' }}>1</td>
                <td style={{ padding: '12px' }}>$1,400.00</td>
                <td style={{ padding: '12px' }}><span className="badge badge-red">STOLEN</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
