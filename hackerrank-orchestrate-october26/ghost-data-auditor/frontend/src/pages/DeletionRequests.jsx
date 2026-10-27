import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getRequests } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function DeletionRequests() {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const perPage = 20;

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getRequests({ q: query, status, page, per_page: perPage });
      setItems(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      setError(err.message || 'Failed to load requests from backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [query, status, page]);


  const pages = useMemo(() => Math.max(1, Math.ceil(total / perPage)), [total]);

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="eyebrow">Request queue</div>
          <h1>Deletion requests</h1>
        </div>
      </div>

      <div className="filters-row">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by case ID or email" />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="COMPLETE">COMPLETE</option>
          <option value="INCOMPLETE">INCOMPLETE</option>
          <option value="NOT_APPLICABLE">NOT_APPLICABLE</option>
        </select>
      </div>

      {error && (
        <div className="alert-banner error" style={{ margin: '1rem 0' }}>
          <span>{error}</span>
          <button className="secondary-button" onClick={fetchData}>Retry</button>
        </div>
      )}

      {loading ? <div className="empty-state">Loading requests…</div> : (

        <div className="panel">
          <table className="data-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Email</th>
                <th>Requested</th>
                <th>Status</th>
                <th>Findings</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.case_id}>
                  <td>{item.case_id}</td>
                  <td>{item.email}</td>
                  <td>{item.requested_at || '—'}</td>
                  <td><StatusBadge status={item.deletion_status} /></td>
                  <td>{item.findings_count}</td>
                  <td><Link to={`/requests/${item.case_id}`}>View</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination-row">
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
            <span>Page {page} / {pages}</span>
            <button disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
