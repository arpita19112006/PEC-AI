import { NavLink } from 'react-router-dom';

const items = [
  { label: 'Dashboard', to: '/' },
  { label: 'Deletion Requests', to: '/requests' },
  { label: 'Request Details', to: '/requests/case_01' },
  { label: 'Evidence Explorer', to: '/evidence' },
  { label: 'Remediation Center', to: '/remediation' },
  { label: 'Evaluation', to: '/evaluation' },
  { label: 'Settings', to: '/settings' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">Operations</div>
      <nav className="sidebar-nav">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
