import { useEffect, useState } from 'react';
import { getRemediation } from '../api/client';

export default function Remediation() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    getRemediation()
      .then((res) => setItems(res.data.items || []))
      .catch((err) => setError(err.message || 'Failed to load remediation data'))
      .finally(() => setLoading(false));
  }, []);


  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="eyebrow">Remediation planner</div>
          <h1>Remediation center</h1>
        </div>
      </div>

      <div className="panel">
        {error ? (
          <div className="alert-banner error">{error}</div>
        ) : loading ? (
          <div className="empty-state">Loading remediation plans…</div>
        ) : items.length === 0 ? (
          <div className="empty-state">No unresolved remediation items found.</div>
        ) : items.map((item) => (

          <div key={item.case_id} className="remediation-card">
            <h3>{item.case_id}</h3>
            <div className="detail-grid">
              <div><strong>Findings:</strong> {item.findings_count}</div>
            </div>
            <ul className="timeline">
              {(item.remediation_steps || []).map((step, index) => (
                <li key={`${item.case_id}-${index}`}>
                  {step.operation} — {step.system_id} / {step.resource_id} ({step.state})
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
