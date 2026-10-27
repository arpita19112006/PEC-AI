import { useEffect, useState } from 'react';
import { getEvidence, searchEvidence } from '../api/client';

export default function EvidenceExplorer() {
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  useEffect(() => {
    getEvidence({ page: 1, per_page: 25 }).then((res) => setItems(res.data.items || []));
  }, []);

  const handleSearch = async () => {
    if (!query) return;
    const res = await searchEvidence(query);
    setResults(res.data.results || []);
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="eyebrow">Evidence corpus</div>
          <h1>Evidence explorer</h1>
        </div>
      </div>

      <div className="filters-row">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search evidence text" />
        <button className="primary-button" onClick={handleSearch}>Search</button>
      </div>

      <div className="panel">
        <h3>Evidence file list</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>file_id</th>
              <th>path</th>
              <th>origin</th>
              <th>captured</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.file_id}>
                <td>{item.file_id}</td>
                <td>{item.file_path}</td>
                <td>{item.origin}</td>
                <td>{item.captured_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {results.length > 0 && (
        <div className="panel">
          <h3>Matches</h3>
          <ul className="timeline">
            {results.map((result) => (
              <li key={`${result.file_id}-${result.snippet}`}>
                <strong>{result.file_id}</strong> — {result.file_path}
                <div className="snippet">{result.snippet}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
