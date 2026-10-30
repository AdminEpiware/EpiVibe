import { ArrowRight, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function CreateEventCard() {
  return (
    <section className="epi-home-hero" aria-label="Create an event">
      <div className="epi-home-hero-content">
        <h2>Plan Your<br /><span>Next Event</span></h2>
        <Link className="epi-home-create" to="/events/new">
          <Plus size={23} aria-hidden="true" />
          <span>Create New Event</span>
          <ArrowRight size={21} aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
