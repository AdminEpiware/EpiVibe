import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import LandingPage from '../../modules/landing/LandingPage';

/** Temporary destination only; replace with the Event Brief module when ready. */
function EventBriefPlaceholder() {
  return (
    <main className="min-h-screen bg-white p-10 text-slate-900">
      <h1 className="text-3xl font-bold">Event Brief</h1>
      <p className="mt-4">The Event Brief module will be connected here.</p>
      <Link to="/" className="mt-6 inline-block text-violet-700 underline">Back to landing</Link>
    </main>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/events/new" element={<EventBriefPlaceholder />} />
      </Routes>
    </BrowserRouter>
  );
}
