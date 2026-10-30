import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import './app-shell.css';

/** Shared application frame. Brand artwork is part of the background image. */
export default function AppShell() {
  return (
    <div className="epi-shell">
      <aside className="epi-shell-sidebar">
        <div className="epi-brand-spacer" aria-label="EpiVibe — AI Event Strategist" />
        <Sidebar />
      </aside>
      <main className="epi-shell-workspace" id="main-content">
        <Outlet />
      </main>
    </div>
  );
}
