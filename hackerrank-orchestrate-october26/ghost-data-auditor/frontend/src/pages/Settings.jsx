export default function Settings() {
  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="eyebrow">Configuration</div>
          <h1>Settings</h1>
        </div>
      </div>

      <div className="panel">
        <h3>Dataset and audit configuration</h3>
        <div className="detail-grid">
          <div><strong>Dataset path:</strong> ./dataset</div>
          <div><strong>Evidence directory:</strong> ./dataset/evidence</div>
          <div><strong>Output CSV:</strong> ./output.csv</div>
          <div><strong>Model provider:</strong> local policy engine</div>
          <div><strong>Backend:</strong> Flask on 127.0.0.1:5000</div>
          <div><strong>Frontend:</strong> Vite on 127.0.0.1:5173</div>
        </div>
      </div>
    </div>
  );
}
