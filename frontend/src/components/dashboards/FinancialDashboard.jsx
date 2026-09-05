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
            Specialist: Financial Auditor • Department: Financial Crimes Division
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
            Financial Exhibits Deposited
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: financialEvidence.length > 0 ? '#dc2626' : 'var(--text-main)' }}>
            {financialEvidence.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Ledgers and transaction streams
          </div>
        </div>

        <div className="card" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Total Ingested Evidence
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {evidence.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--success-text)', fontWeight: 600, marginTop: '4px' }}>
            Cryptographically sealed
          </div>
        </div>

        <div className="card" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Reconciliation Status
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: financialEvidence.length > 0 ? '#10b981' : 'var(--text-muted)' }}>
            {financialEvidence.length > 0 ? 'ACTIVE' : 'IDLE'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Awaiting FI01-FI07 engine execution
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
              <tr>
                <td colSpan="5" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No inventory ledger items ingested yet. Deposit an inventory CSV in the Evidence Vault to reconcile stock discrepancies.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
