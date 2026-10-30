import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import LandingPage from '../modules/landing/LandingPage';
import HomeContent from '../modules/home/HomeContent';
import AppShell from '../shared/layout/AppShell';
import EventBriefContent from '../modules/event-brief/EventBriefContent';
import ProjectsContent from '../modules/home/components/ProjectsContent';
import ProjectOverview from '../modules/home/components/ProjectOverview';
import ResearchPage from '../modules/research/ResearchPage';
import ConceptPage from '../modules/event-concept/ConceptPage';
import RefinementPage from '../modules/ai-refinement/RefinementPage';
import ExecutionPlanPage from '../modules/execution-plan/ExecutionPlanPage';

export default function App() {
  return <BrowserRouter><Routes>
    <Route path="/" element={<LandingPage />} />
    <Route element={<AppShell />}>
      <Route path="/home" element={<HomeContent />} />
      <Route path="/events/new" element={<EventBriefContent />} />
      <Route path="/events/:id/edit" element={<EventBriefContent />} />
      <Route path="/projects" element={<ProjectsContent />} />
      <Route path="/projects/:id" element={<ProjectOverview />} />
      <Route path="/projects/:id/research" element={<ResearchPage />} />
      <Route path="/projects/:id/concept" element={<ConceptPage />} />
      <Route path="/projects/:id/refine" element={<RefinementPage />} />
      <Route path="/projects/:id/execution" element={<ExecutionPlanPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></BrowserRouter>;
}
