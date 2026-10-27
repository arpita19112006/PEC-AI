import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getRequestDetail } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function RequestDetails() {
  const { caseId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null);
    getRequestDetail(caseId)
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.error || err.message || 'Failed to load case details'));
  }, [caseId]);

  if (error) return (
    <div className="page-shell">
      <div className="alert-banner error">
        <span>Error loading case {caseId}: {error}</span>
      </div>
    </div>
  );

  if (!data) return <div className="empty-state">Loading case details…</div>;


  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="eyebrow">Case review</div>
          <h1>{data.case_id}</h1>
        </div>
        <StatusBadge status={data.deletion_status} />
      </div>

      <div className="panel">
        <h3>Request details</h3>
        <div className="detail-grid">
          <div><strong>Email:</strong> {data.request?.email}</div>
          <div><strong>Requested:</strong> {data.request?.requested_at}</div>
          <div><strong>Audit time:</strong> {data.request?.audit_at}</div>
          <div><strong>Reported status:</strong> {data.request?.reported_status}</div>
        </div>
      </div>

      <div className="panel">
        <h3>Findings</h3>
        {data.findings.length === 0 ? <div className="empty-state">No unresolved findings.</div> : (
          <ul className="timeline">
            {data.findings.map((item) => (
              <li key={`${item.system_id}-${item.resource_id}-${item.operation}`}>
                <strong>{item.operation}</strong> — {item.system_id} / {item.resource_id} ({item.state})
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="panel">
        <h3>Remediation</h3>
        {data.remediation.length === 0 ? <div className="empty-state">No remediation required.</div> : (
          <ul className="timeline">
            {data.remediation.map((item) => (
              <li key={`${item.system_id}-${item.operation}-${item.resource_id}`}>
                {item.operation} / {item.state} — {item.system_id} / {item.resource_id}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
