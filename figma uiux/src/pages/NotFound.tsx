import { Link } from 'react-router';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <p className="text-7xl font-bold text-slate-200 mb-4" style={{ fontFamily: 'var(--font-display)' }}>404</p>
      <h1 className="text-2xl font-semibold text-slate-700 mb-2" style={{ fontFamily: 'var(--font-display)' }}>Page not found</h1>
      <p className="text-slate-500 text-sm mb-6 max-w-sm">This page doesn't exist or has been moved. Use the navigation to find what you're looking for.</p>
      <Link
        to="/forum"
        className="px-5 py-2.5 text-sm font-semibold text-white rounded-xl"
        style={{ backgroundColor: '#1E3A8A' }}
      >
        Go to Forum
      </Link>
    </div>
  );
}
