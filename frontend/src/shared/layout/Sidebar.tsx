import { NavLink } from 'react-router-dom';
import { sidebarItems } from '../../config/sidebar.config';

export default function Sidebar() {
  return (
    <nav className="epi-sidebar-nav" aria-label="Main navigation">
      {sidebarItems.map(({ label, path, icon: Icon }) => (
        <NavLink key={path} to={path} end={path === '/home'}
          className={({ isActive }) => `epi-sidebar-link${isActive ? ' is-active' : ''}`}>
          <Icon aria-hidden="true" size={18} strokeWidth={2} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
