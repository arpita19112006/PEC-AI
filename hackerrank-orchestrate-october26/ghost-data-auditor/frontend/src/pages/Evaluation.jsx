import { useEffect, useState } from 'react';
import { getEvaluationReport } from '../api/client';

export default function Evaluation() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null);
    getEvaluationReport()
      .then((res) => setReport(res.data))
      .catch((err) => setError(err.message || 'Failed to load evaluation report'));
  }, []);

  if (error) return (
    <div className="page-shell">
      <div className="alert-banner error">{error}</div>
    </div>
  );

  if (!report) return <div className="empty-state">Loading evaluation report…</div>;


  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="eyebrow">Validation</div>
          <h1>Evaluation</h1>
        </div>
      </div>

      <div className="summary-grid">
        <div className="stat-card"><div className="stat-label">Requests evaluated</div><div className="stat-value">{report.total_evaluated ?? 0}</div></div>
        <div className="stat-card"><div className="stat-label">Correct</div><div className="stat-value">{report.correct ?? 0}</div></div>
        <div className="stat-card"><div className="stat-label">Accuracy</div><div className="stat-value">{report.accuracy ?? 0}</div></div>
      </div>

      <div className="panel">
        <h3>Per-class metrics</h3>
        <table className="data-table">
          <thead>
            <tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th></tr>
          </thead>
          <tbody>
            {Object.entries(report.per_class || {}).map(([key, value]) => (
              <tr key={key}><td>{key}</td><td>{value.precision}</td><td>{value.recall}</td><td>{value.f1}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
