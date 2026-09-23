import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { getQuestionById, getAnswersByQuestionId, voteOnTarget, getUserVote, submitAnswer } from '../services/forum';
import { getUserById } from '../services/auth';
import type { Question, Answer, User } from '../types';
import { getCategoryById, getTagById } from '../data/categories';
import Avatar from '../components/common/Avatar';
import Badge from '../components/common/Badge';
import VoteControls from '../components/forum/VoteControls';
import AnswerCard from '../components/forum/AnswerCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { formatFullDate, formatRelativeDate } from '../utils/date';

export default function QuestionThread() {
  const { id } = useParams<{ id: string }>();
  const { currentUser, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [question, setQuestion] = useState<Question | null>(null);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [questionAuthor, setQuestionAuthor] = useState<User | undefined>();
  const [loading, setLoading] = useState(true);
  const [answerSort, setAnswerSort] = useState<'votes' | 'latest'>('votes');
  const [answerBody, setAnswerBody] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [questionVote, setQuestionVote] = useState<1 | -1 | 0>(0);
  const [answerVotes, setAnswerVotes] = useState<Record<string, 1 | -1 | 0>>({});

  async function loadData() {
    if (!id) return;
    setLoading(true);
    const [qRes, aRes] = await Promise.all([
      getQuestionById(id),
      getAnswersByQuestionId(id),
    ]);
    if (!qRes.success || !qRes.data) { navigate('/forum'); return; }
    setQuestion(qRes.data);
    setQuestionAuthor(getUserById(qRes.data.authorId));
    setAnswers(aRes.data || []);
    if (currentUser) {
      setQuestionVote(getUserVote(currentUser.id, id));
      const voteMap: Record<string, 1 | -1 | 0> = {};
      (aRes.data || []).forEach(a => { voteMap[a.id] = getUserVote(currentUser.id, a.id); });
      setAnswerVotes(voteMap);
    }
    setLoading(false);
  }

  useEffect(() => { loadData(); }, [id]);

  async function handleQuestionVote(value: 1 | -1) {
    if (!currentUser || !question) return;
    const result = await voteOnTarget(currentUser.id, question.id, 'question', value);
    if (result.success && result.data) {
      setQuestion(q => q ? { ...q, upvotes: result.data!.upvotes, downvotes: result.data!.downvotes } : q);
      setQuestionVote(getUserVote(currentUser.id, question.id));
    }
  }

  async function handleAnswerVote(answerId: string, value: 1 | -1) {
    if (!currentUser) return;
    const result = await voteOnTarget(currentUser.id, answerId, 'answer', value);
    if (result.success && result.data) {
      setAnswers(prev => prev.map(a => a.id === answerId ? { ...a, upvotes: result.data!.upvotes, downvotes: result.data!.downvotes } : a));
      setAnswerVotes(prev => ({ ...prev, [answerId]: getUserVote(currentUser.id, answerId) }));
    }
  }

  async function handleSubmitAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!answerBody.trim() || answerBody.length < 10) return setSubmitError('Answer must be at least 10 characters.');
    if (!currentUser || !question) return;
    setSubmitError('');
    setSubmitLoading(true);
    const result = await submitAnswer({ questionId: question.id, body: answerBody.trim(), authorId: currentUser.id });
    setSubmitLoading(false);
    if (result.success) {
      setAnswerBody('');
      setSubmitSuccess(true);
      await loadData();
      setTimeout(() => setSubmitSuccess(false), 3000);
    }
  }

  const sortedAnswers = [...answers].sort((a, b) =>
    answerSort === 'votes'
      ? (b.upvotes - b.downvotes) - (a.upvotes - a.downvotes)
      : new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size={36} className="text-blue-700" />
      </div>
    );
  }

  if (!question) return null;

  const category = getCategoryById(question.categoryId);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <Link to="/forum" className="hover:text-blue-700 transition-colors">Forum</Link>
        <span>›</span>
        {category && <Link to={`/forum?category=${category.id}`} className="hover:text-blue-700 transition-colors">{category.name}</Link>}
        {category && <span>›</span>}
        <span className="text-slate-700 truncate max-w-xs">{question.title}</span>
      </nav>

      {/* Question */}
      <article className="bg-white border border-slate-200 rounded-2xl p-6 mb-6">
        <div className="flex gap-5">
          <VoteControls
            upvotes={question.upvotes}
            downvotes={question.downvotes}
            userVote={questionVote}
            onVote={handleQuestionVote}
            disabled={!isAuthenticated}
          />
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap gap-2 mb-3">
              {question.isAnswered && (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
                  <svg width="10" height="10" viewBox="0 0 16 16" fill="none"><path d="M3 8l3.5 3.5 6.5-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  Answered
                </span>
              )}
              {category && <Badge label={category.name} color="#1E3A8A" variant="soft" />}
            </div>

            <h1 className="text-2xl text-slate-800 leading-snug mb-4" style={{ fontFamily: 'var(--font-display)' }}>
              {question.title}
            </h1>

            <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line mb-5">
              {question.body}
            </div>

            <div className="flex flex-wrap gap-1.5 mb-5">
              {question.tags.map(tagId => {
                const tag = getTagById(tagId);
                return tag ? <Badge key={tagId} label={tag.name} color={tag.color} variant="outline" /> : null;
              })}
            </div>

            <div className="flex items-center justify-between flex-wrap gap-3 pt-4 border-t border-slate-100">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span>{question.views} views</span>
                <span>·</span>
                <span>Asked {formatFullDate(question.createdAt)}</span>
              </div>
              {questionAuthor && (
                <Link to={`/profile/${questionAuthor.id}`} className="flex items-center gap-2 text-sm text-slate-600 hover:text-blue-700 transition-colors">
                  <Avatar user={questionAuthor} size="sm" />
                  <div>
                    <p className="font-medium leading-tight">{questionAuthor.fullName}</p>
                    <p className="text-xs text-slate-400">@{questionAuthor.username}</p>
                  </div>
                </Link>
              )}
            </div>
          </div>
        </div>
      </article>

      {/* Answers */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-800">
            {answers.length} {answers.length === 1 ? 'Answer' : 'Answers'}
          </h2>
          <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg p-1">
            {(['votes', 'latest'] as const).map(s => (
              <button
                key={s}
                onClick={() => setAnswerSort(s)}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${answerSort === s ? 'bg-slate-100 text-slate-800' : 'text-slate-500 hover:text-slate-700'}`}
              >
                {s === 'votes' ? 'Top Voted' : 'Latest'}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3 mb-8">
          {sortedAnswers.map(answer => (
            <AnswerCard
              key={answer.id}
              answer={answer}
              author={getUserById(answer.authorId)}
              userVote={answerVotes[answer.id] || 0}
              onVote={v => handleAnswerVote(answer.id, v)}
              canVote={isAuthenticated}
            />
          ))}
          {answers.length === 0 && (
            <div className="text-center py-10 bg-white border border-slate-200 rounded-xl">
              <p className="text-slate-500 text-sm">No answers yet. Be the first to help!</p>
            </div>
          )}
        </div>

        {/* Submit answer */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6">
          <h3 className="text-base font-semibold text-slate-800 mb-4" style={{ fontFamily: 'var(--font-display)' }}>Your Answer</h3>

          {isAuthenticated ? (
            <form onSubmit={handleSubmitAnswer}>
              <textarea
                value={answerBody}
                onChange={e => { setAnswerBody(e.target.value); setSubmitError(''); }}
                placeholder="Share your knowledge or experience…"
                rows={6}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors resize-none mb-3"
              />
              {submitError && <p className="text-xs text-red-600 mb-3">{submitError}</p>}
              {submitSuccess && (
                <p className="text-xs text-green-700 bg-green-50 rounded-lg px-3 py-2 mb-3">Your answer was posted successfully!</p>
              )}
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={submitLoading}
                  className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white rounded-xl disabled:opacity-60"
                  style={{ backgroundColor: '#1E3A8A' }}
                >
                  {submitLoading && <LoadingSpinner size={14} />}
                  Post Answer
                </button>
              </div>
            </form>
          ) : (
            <div className="text-center py-6">
              <p className="text-slate-600 text-sm mb-4">Sign in to share your answer with the community.</p>
              <Link
                to="/?mode=signin"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white rounded-xl"
                style={{ backgroundColor: '#1E3A8A' }}
              >
                Sign in to answer
              </Link>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
