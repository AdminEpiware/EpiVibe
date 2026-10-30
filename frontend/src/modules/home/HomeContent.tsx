import WelcomePanel from './components/WelcomePanel';
import CreateEventCard from './components/CreateEventCard';
import ProjectList from './components/ProjectList';
import './home.css';

export default function HomeContent() {
  return <div className="epi-home"><WelcomePanel /><CreateEventCard /><ProjectList /></div>;
}
