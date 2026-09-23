import { createBrowserRouter, Outlet } from 'react-router';
import Navbar from './components/layout/Navbar';
import Home from './pages/Home';
import Forum from './pages/Forum';
import QuestionThread from './pages/QuestionThread';
import Profile from './pages/Profile';
import Chatbot from './pages/Chatbot';
import NotFound from './pages/NotFound';

function Root() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <Outlet />
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Root,
    children: [
      { index: true, Component: Home },
      { path: 'forum', Component: Forum },
      { path: 'forum/:id', Component: QuestionThread },
      { path: 'profile/:id', Component: Profile },
      { path: 'chatbot', Component: Chatbot },
      { path: '*', Component: NotFound },
    ],
  },
]);
