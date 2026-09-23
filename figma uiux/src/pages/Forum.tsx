import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { getQuestions } from '../services/forum';
import { getUserById } from '../services/auth';
import type { Question, ForumFilters } from '../types';
import { CATEGORIES } from '../data/categories';
import QuestionCard from '../components/forum/QuestionCard';
import AskQuestionModal from '../components/forum/AskQuestionModal';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function Forum() {
  const { isAuthenticated } = useAuth();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAsk, setShowAsk] = useState(false);
  const [filters, setFilters] = useState<ForumFilters>({
    search: '',
    categoryId: null,
    sortBy: 'latest',
    answered: 'all',
  });

  async function loadQuestions() {
    setLoading(true);
    const result = await getQuestions();
    if (result.success && result.data) setQuestions(result.data);
    setLoading(false);
  }

  useEffect(() => { loadQuestions(); }, []);

  const filtered = useMemo(() => {
    let qs = [...questions];
    if (filters.search) {
      const q = filters.search.toLowerCase();
      qs = qs.filter(q2 =>
        q2.title.toLowerCase().includes(q) ||
        q2.body.toLowerCase().includes(q) ||
        q2.tags.some(t => t.includes(q))
      );
    }
    if (filters.categoryId) qs = qs.filter(q => q.categoryId === filters.categoryId);
    if (filters.answered === 'answered') qs = qs.filter(q => q.isAnswered);
    if (filters.answered === 'unanswered') qs = qs.filter(q => !q.isAnswered);
    switch (filters.sortBy) {
      case 'most-upvoted': qs.sort((a, b) => (b.upvotes - b.downvotes) - (a.upvotes - a.downvotes)); break;
      case 'most-answered': qs.sort((a, b) => b.answerCount - a.answerCount); break;
      default: qs.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    }
    return qs;
  }, [questions, filters]);

  const hasActiveFilters = filters.categoryId || filters.answered !== 'all' || filters.sortBy !== 'latest' || filters.search;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl text-slate-800 mb-1" style={{ fontFamily: 'var(--font-display)' }}>Community Forum</h1>
          <p className="text-slate-500 text-sm">Ask questions, share knowledge, help newcomers navigate Bennett.</p>
        </div>
        {isAuthenticated ? (
          <button
            onClick={() => setShowAsk(true)}
            className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white rounded-xl transition-colors flex-shrink-0"
            style={{ backgroundColor: '#1E3A8A' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>
            Ask a Question
          </button>
        ) : (
          <Link
            to="/?mode=signup"
            className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white rounded-xl transition-colors flex-shrink-0"
            style={{ backgroundColor: '#1E3A8A' }}
          >
            Sign up to ask
          </Link>
        )}
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar filters */}
        <aside className="lg:w-64 flex-shrink-0">
          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-5 sticky top-20">
            {/* Sort */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Sort by</p>
              <div className="space-y-1">
                {([['latest', 'Latest'], ['most-upvoted', 'Most Upvoted'], ['most-answered', 'Most Answered']] as const).map(([val, label]) => (
                  <button
                    key={val}
                    onClick={() => setFilters(f => ({ ...f, sortBy: val }))}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${filters.sortBy === val ? 'bg-blue-50 text-blue-800 font-medium' : 'text-slate-600 hover:bg-slate-50'}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Status */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Status</p>
              <div className="space-y-1">
                {([['all', 'All Questions'], ['answered', 'Answered'], ['unanswered', 'Unanswered']] as const).map(([val, label]) => (
                  <button
                    key={val}
                    onClick={() => setFilters(f => ({ ...f, answered: val }))}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${filters.answered === val ? 'bg-blue-50 text-blue-800 font-medium' : 'text-slate-600 hover:bg-slate-50'}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Academic categories */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Academic</p>
              <div className="space-y-1">
                {CATEGORIES.filter(c => c.type === 'academic').map(c => (
                  <button
                    key={c.id}
                    onClick={() => setFilters(f => ({ ...f, categoryId: f.categoryId === c.id ? null : c.id }))}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${filters.categoryId === c.id ? 'bg-blue-50 text-blue-800 font-medium' : 'text-slate-600 hover:bg-slate-50'}`}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Non-academic categories */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Non-academic</p>
              <div className="space-y-1">
                {CATEGORIES.filter(c => c.type === 'non-academic').map(c => (
                  <button
                    key={c.id}
                    onClick={() => setFilters(f => ({ ...f, categoryId: f.categoryId === c.id ? null : c.id }))}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${filters.categoryId === c.id ? 'bg-blue-50 text-blue-800 font-medium' : 'text-slate-600 hover:bg-slate-50'}`}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            </div>

            {hasActiveFilters && (
              <button
                onClick={() => setFilters({ search: '', categoryId: null, sortBy: 'latest', answered: 'all' })}
                className="w-full text-center text-xs text-red-600 hover:text-red-700 font-medium py-1"
              >
                Clear all filters
              </button>
            )}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          {/* Search bar */}
          <div className="relative mb-5">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            <input
              type="search"
              value={filters.search}
              onChange={e => setFilters(f => ({ ...f, search: e.target.value }))}
              placeholder="Search questions…"
              className="w-full pl-11 pr-4 py-3 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors"
            />
          </div>

          {/* Stats bar */}
          <div className="flex items-center justify-between mb-4 px-1">
            <p className="text-sm text-slate-500">
              <span className="font-semibold text-slate-700">{filtered.length}</span> question{filtered.length !== 1 ? 's' : ''}
              {hasActiveFilters && ' matching filters'}
            </p>
          </div>

          {/* Questions list */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <LoadingSpinner size={32} className="text-blue-700" />
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              icon="🔍"
              title="No questions found"
              description="Try adjusting your filters or be the first to ask about this topic."
              action={
                isAuthenticated ? (
                  <button
                    onClick={() => setShowAsk(true)}
                    className="px-5 py-2.5 text-sm font-semibold text-white rounded-xl"
                    style={{ backgroundColor: '#1E3A8A' }}
                  >
                    Ask a Question
                  </button>
                ) : undefined
              }
            />
          ) : (
            <div className="space-y-3">
              {filtered.map(q => (
                <QuestionCard key={q.id} question={q} author={getUserById(q.authorId)} />
              ))}
            </div>
          )}
        </main>
      </div>

      {showAsk && (
        <AskQuestionModal
          onClose={() => setShowAsk(false)}
          onSuccess={() => { setShowAsk(false); loadQuestions(); }}
        />
      )}
    </div>
  );
}
