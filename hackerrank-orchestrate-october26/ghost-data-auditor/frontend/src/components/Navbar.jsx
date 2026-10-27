import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="topbar">
      <div className="brand-wrap">
        <div className="brand-badge">G</div>
        <div>
          <div className="brand-name">Ghost Data Auditor</div>
          <div className="brand-subtitle">Deletion risk and policy validation</div>
        </div>
      </div>
      <div className="topbar-actions">
        <Link className="nav-link" to="/">Dashboard</Link>
        <Link className="nav-link" to="/requests">Requests</Link>
        <Link className="nav-link" to="/settings">Settings</Link>
      </div>
    </nav>
  );
}
