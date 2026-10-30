import { FolderOpen, House, PlusSquare } from 'lucide-react';
export const sidebarItems = [
  { label: 'Home', path: '/home', icon: House },
  { label: 'New Event', path: '/events/new', icon: PlusSquare },
  { label: 'Projects', path: '/projects', icon: FolderOpen },
] as const;
