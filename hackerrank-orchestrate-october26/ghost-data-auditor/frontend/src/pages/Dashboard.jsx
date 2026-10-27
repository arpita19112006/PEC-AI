import { useEffect, useState, useRef, useCallback } from 'react';
import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { getDashboardStats, getRequests, runAudit, getAuditStatus, getHealth } from '../api/client';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const [auditRunning, setAuditRunning] = useState(false);
  const [auditProgress, setAuditProgress] = useState({ progress: 0, total: 518 });
  const pollTimerRef = useRef(null);

  // Stop polling helper
  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  // Polling loop for active audit
  const startAuditPolling = useCallback(() => {
    stopPolling();
    setAuditRunning(true);

    pollTimerRef.current = setInterval(async () => {
      try {
        const res = await getAuditStatus();
        const data = res.data;
        const current = data.progress || 0;
        const total = data.total || 518;
        setAuditProgress({ progress: current, total });

        if (data.status === 'complete') {
          stopPolling();
          setAuditRunning(false);
          setSuccessMessage('Deletion audit completed successfully! Output CSV and statistics updated.');
          // Refresh dashboard data after audit finishes
          loadData();
        } else if (data.status === 'error') {
          stopPolling();
          setAuditRunning(false);
          setError(`Audit run failed: ${data.error || 'Unknown error occurred'}`);
        }
      } catch (err) {
        console.error('Error polling audit status:', err);
      }
    }, 1000);
  }, [stopPolling]);

  // Main data loader
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, reqRes, healthRes, auditStatusRes] = await Promise.all([
        getDashboardStats().catch((err) => ({ error: err })),
        getRequests({ page: 1, per_page: 8 }).catch((err) => ({ error: err })),
        getHealth().catch((err) => ({ error: err })),
        getAuditStatus().catch((err) => ({ error: err })),
      ]);

      if (healthRes.error && statsRes.error) {
        throw new Error(
          'Cannot connect to Flask backend at http://127.0.0.1:5000. ' +
          'Please ensure the backend is running using: python ghost-data-auditor/backend/app.py'
        );
      }

      if (statsRes.data) {
        setStats(statsRes.data);
      }
      if (reqRes.data) {
        setRequests(reqRes.data.items || []);
      }
      if (healthRes.data) {
        setHealth(healthRes.data);
      }

      // Check if an audit is already running
      if (auditStatusRes.data && auditStatusRes.data.status === 'running') {
        const current = auditStatusRes.data.progress || 0;
        const total = auditStatusRes.data.total || 518;
        setAuditProgress({ progress: current, total });
        startAuditPolling();
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Failed to load dashboard data from backend');
    } finally {
      setLoading(false);
    }
  }, [startAuditPolling]);

  useEffect(() => {
    loadData();
    return () => stopPolling();
  }, [loadData, stopPolling]);

  // Handle clicking "Run audit"
  const handleRunAudit = async () => {
    setError(null);
    setSuccessMessage(null);
    setAuditRunning(true);
    setAuditProgress({ progress: 0, total: 518 });
    try {
      const res = await runAudit();
      if (res.data?.status === 'started' || res.status === 200) {
        startAuditPolling();
      }
    } catch (err) {
      setAuditRunning(false);
      const errMsg = err.response?.data?.error || err.message || 'Failed to start audit';
      setError(`Failed to start audit: ${errMsg}`);
    }
  };

  const chartData = [
    { name: 'Complete', value: Number(stats?.complete || 0) },
    { name: 'Incomplete', value: Number(stats?.incomplete || 0) },
    { name: 'Not applicable', value: Number(stats?.not_applicable || 0) },
  ];

  const progressPercent = auditProgress.total > 0
    ? Math.min(100, Math.round((auditProgress.progress / auditProgress.total) * 100))
    : 0;

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="eyebrow">Privacy operations overview</div>
          <h1>Deletion audit dashboard</h1>
        </div>
        <div className="header-actions">
          <button
            className="primary-button"
            onClick={handleRunAudit}
            disabled={auditRunning || loading}
          >
            {auditRunning
              ? `Running audit (${auditProgress.progress}/${auditProgress.total})…`
              : 'Run audit'}
          </button>
          <a
            className="secondary-button"
            href="http://127.0.0.1:5000/api/output/download"
            target="_blank"
            rel="noreferrer"
          >
            Download output CSV
          </a>
        </div>
      </div>

      {/* Audit Running Progress Bar */}
      {auditRunning && (
        <div className="alert-banner info">
          <div className="progress-container">
            <div className="progress-label">
              <span><strong>Audit in progress:</strong> Processing deletion requests against evidence...</span>
              <span>{auditProgress.progress} / {auditProgress.total} ({progressPercent}%)</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>
        </div>
      )}

      {/* Error Banner with Retry */}
      {error && (
        <div className="alert-banner error">
          <span>{error}</span>
          <button className="secondary-button" onClick={loadData}>Retry</button>
        </div>
      )}

      {/* Success Banner */}
      {successMessage && (
        <div className="alert-banner success">
          <span>{successMessage}</span>
          <button
            className="secondary-button"
            style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
            onClick={() => setSuccessMessage(null)}
          >
            ✕
          </button>
        </div>
      )}

      {/* Summary Statistics Cards */}
      <div className="summary-grid">
        <StatCard label="Total requests" value={stats?.total_requests ?? (loading ? '…' : 0)} tone="default" />
        <StatCard label="Complete" value={stats?.complete ?? (loading ? '…' : 0)} tone="success" />
        <StatCard label="Incomplete" value={stats?.incomplete ?? (loading ? '…' : 0)} tone="warning" />
        <StatCard label="Not applicable" value={stats?.not_applicable ?? (loading ? '…' : 0)} tone="neutral" />
        <StatCard label="Awaiting investigation" value={stats?.awaiting_investigation ?? (loading ? '…' : 0)} tone="default" />
        <StatCard label="Remaining personal-data copies" value={stats?.total_findings ?? (loading ? '…' : 0)} tone="alert" />
        <StatCard label="Live sync / restore risks" value={stats?.active_risks ?? (loading ? '…' : 0)} tone="alert" />
        <StatCard label="Policy violations" value={stats?.policy_violations ?? (loading ? '…' : 0)} tone="warning" />
      </div>

      <div className="two-column-grid">
        <div className="panel chart-panel">
          <h3>Status distribution</h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#6ea8fe" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel chart-panel">
          <h3>System health</h3>
          <div className="health-box">
            <div>
              <strong>Backend Status: </strong>
              <span style={{ color: health?.status === 'ok' ? '#86efac' : '#fca5a5' }}>
                {health?.status ? health.status.toUpperCase() : (loading ? 'Connecting…' : 'DISCONNECTED')}
              </span>
            </div>
            <div>
              <strong>Dataset: </strong>
              {health?.checks?.dataset_exists ? 'Connected (deletion_requests.csv)' : 'Missing'}
            </div>
            <div>
              <strong>Output CSV: </strong>
              {health?.checks?.output_exists ? 'Available (output.csv generated)' : 'Not generated'}
            </div>
            <div>
              <strong>Audit status: </strong>
              {auditRunning
                ? `Running (${auditProgress.progress}/${auditProgress.total})`
                : (stats?.audit_status || health?.checks?.audit_status || 'idle')}
            </div>
            {health?.checks?.python_version && (
              <div>
                <strong>Engine: </strong>
                Python {health.checks.python_version.split(' ')[0]}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' }}>
          <h3>Recent requests</h3>
          {requests.length > 0 && <span style={{ color: '#9fb8d9', fontSize: '0.85rem' }}>Showing first {requests.length} of {stats?.total_requests || 518}</span>}
        </div>

        {loading && requests.length === 0 ? (
          <div className="empty-state">Loading requests from backend…</div>
        ) : requests.length === 0 ? (
          <div className="empty-state">No requests found. Check backend connection.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Status</th>
                <th>Findings</th>
                <th>Requested</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((row) => (
                <tr key={row.case_id}>
                  <td><strong>{row.case_id}</strong></td>
                  <td><StatusBadge status={row.deletion_status} /></td>
                  <td>{row.findings_count}</td>
                  <td>{row.requested_at || row.audit_at || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
