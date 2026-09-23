import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { getUserById, updateUserProfile } from '../services/auth';
import { getQuestions_sync } from '../services/forum';
import { MOCK_ANSWERS } from '../data/questions';
import type { User, Question, Answer } from '../types';
import Avatar from '../components/common/Avatar';
import Badge from '../components/common/Badge';
import QuestionCard from '../components/forum/QuestionCard';
import { formatFullDate, formatRelativeDate } from '../utils/date';
import LoadingSpinner from '../components/common/LoadingSpinner';

type ProfileTab = 'overview' | 'questions' | 'answers';

export default function Profile() {
  const { id } = useParams<{ id: string }>();
  const { currentUser, updateCurrentUser } = useAuth();
  const navigate = useNavigate();
  const [profileUser, setProfileUser] = useState<User | null>(null);
  const [tab, setTab] = useState<ProfileTab>('overview');
  const [editingBio, setEditingBio] = useState(false);
  const [bioValue, setBioValue] = useState('');
  const [savingBio, setSavingBio] = useState(false);
  const isOwner = currentUser?.id === id;
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const user = getUserById(id!);
    if (!user) { navigate('/forum'); return; }
    setProfileUser(user);
    setBioValue(user.bio || '');
    setTab('overview');
  }, [id]);

  async function saveBio() {
    if (!profileUser) return;
    setSavingBio(true);
    const result = await updateUserProfile(profileUser.id, { bio: bioValue });
    setSavingBio(false);
    if (result.success && result.user) {
      setProfileUser(result.user);
      if (isOwner) updateCurrentUser({ bio: bioValue });
    }
    setEditingBio(false);
  }

  const userQuestions = getQuestions_sync().filter(q => q.authorId === id);
  const userAnswers = MOCK_ANSWERS.filter(a => a.authorId === id);

  if (!profileUser) return (
    <div className="flex items-center justify-center py-20">
      <LoadingSpinner size={36} className="text-blue-700" />
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Profile card */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden mb-6">
        {/* Cover bar */}
        <div className="h-20 sm:h-28" style={{ background: `linear-gradient(135deg, ${profileUser.avatarColor}22, ${profileUser.avatarColor}08)`, borderBottom: `1px solid ${profileUser.avatarColor}20` }} />

        <div className="px-6 pb-6">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 -mt-8 sm:-mt-10 mb-5">
            <div className="flex items-end gap-4">
              <div className="relative">
                <Avatar user={profileUser} size="xl" className="border-4 border-white shadow-sm" />
                {isOwner && (
                  <>
                    <button
                      onClick={() => fileRef.current?.click()}
                      className="absolute bottom-0 right-0 w-6 h-6 bg-slate-700 text-white rounded-full flex items-center justify-center hover:bg-slate-800 transition-colors"
                      title="Change avatar"
                    >
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                    </button>
                    <input ref={fileRef} type="file" accept="image/*" className="hidden" aria-label="Upload avatar" />
                  </>
                )}
              </div>
              <div className="pb-1">
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-semibold text-slate-800" style={{ fontFamily: 'var(--font-display)' }}>{profileUser.fullName}</h1>
                  {profileUser.verificationStatus === 'verified' && (
                    <span title="Verified" className="flex items-center">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="11" fill="#1E3A8A" fillOpacity="0.1"/>
                        <path d="M9 12l2 2 4-4" stroke="#1E3A8A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <circle cx="12" cy="12" r="10" stroke="#1E3A8A" strokeWidth="1.5"/>
                      </svg>
                    </span>
                  )}
                </div>
                <p className="text-slate-500 text-sm">@{profileUser.username}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Badge
                label={profileUser.accountType.charAt(0).toUpperCase() + profileUser.accountType.slice(1)}
                color={profileUser.accountType === 'student' ? '#1E3A8A' : profileUser.accountType === 'staff' ? '#059669' : '#64748B'}
                variant="soft"
                size="md"
              />
              {profileUser.verificationStatus === 'verified' && (
                <Badge label="Verified" color="#059669" variant="soft" size="md" />
              )}
              {profileUser.verificationStatus === 'pending' && (
                <Badge label="Verification pending" color="#D97706" variant="soft" size="md" />
              )}
            </div>
          </div>

          {/* Details row */}
          <div className="flex flex-wrap gap-4 text-sm text-slate-500 mb-4">
            {(profileUser.course || profileUser.department) && (
              <span className="flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
                {profileUser.course || profileUser.department}
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              Joined {formatFullDate(profileUser.joinedAt)}
            </span>
          </div>

          {/* Bio */}
          <div className="mb-2">
            {editingBio ? (
              <div>
                <textarea
                  value={bioValue}
                  onChange={e => setBioValue(e.target.value)}
                  rows={3}
                  maxLength={300}
                  className="w-full px-4 py-2.5 rounded-xl border border-blue-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200 resize-none"
                />
                <div className="flex items-center gap-2 mt-2">
                  <button onClick={saveBio} disabled={savingBio} className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-60" style={{ backgroundColor: '#1E3A8A' }}>
                    {savingBio && <LoadingSpinner size={12} />} Save
                  </button>
                  <button onClick={() => { setEditingBio(false); setBioValue(profileUser.bio || ''); }} className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700">Cancel</button>
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-2">
                <p className="text-sm text-slate-600 leading-relaxed flex-1">
                  {profileUser.bio || (isOwner ? <span className="text-slate-400 italic">Add a bio to tell the community about yourself.</span> : <span className="text-slate-400 italic">No bio yet.</span>)}
                </p>
                {isOwner && (
                  <button onClick={() => setEditingBio(true)} className="flex-shrink-0 p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors" title="Edit bio">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {[
          { label: 'Questions', value: profileUser.questionsCount + userQuestions.filter(q => q.authorId !== profileUser.id || MOCK_ANSWERS.some(a => a.authorId === profileUser.id)).length > 0 ? userQuestions.length : profileUser.questionsCount },
          { label: 'Answers', value: userAnswers.length || profileUser.answersCount },
          { label: 'Upvotes received', value: profileUser.upvotesReceived },
        ].map(stat => (
          <div key={stat.label} className="bg-white border border-slate-200 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-slate-800" style={{ fontFamily: 'var(--font-display)' }}>{stat.value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white border border-slate-200 rounded-xl p-1 mb-5 w-fit">
        {(['overview', 'questions', 'answers'] as ProfileTab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all capitalize ${tab === t ? 'bg-slate-100 text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'overview' && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Recent questions</h3>
            {userQuestions.length > 0 ? (
              <div className="space-y-2">
                {userQuestions.slice(0, 3).map(q => (
                  <Link key={q.id} to={`/forum/${q.id}`} className="flex items-start gap-2 text-sm text-slate-700 hover:text-blue-700 transition-colors group py-1">
                    <span className="mt-0.5 flex-shrink-0 text-slate-300 group-hover:text-blue-300">›</span>
                    <span className="line-clamp-1">{q.title}</span>
                  </Link>
                ))}
              </div>
            ) : <p className="text-sm text-slate-400">No questions yet.</p>}
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Recent answers</h3>
            {userAnswers.length > 0 ? (
              <div className="space-y-2">
                {userAnswers.slice(0, 3).map(a => (
                  <Link key={a.id} to={`/forum/${a.questionId}`} className="flex items-start gap-2 text-sm text-slate-700 hover:text-blue-700 transition-colors group py-1">
                    <span className="mt-0.5 flex-shrink-0 text-green-400">✓</span>
                    <span className="line-clamp-1">{a.body.substring(0, 80)}…</span>
                  </Link>
                ))}
              </div>
            ) : <p className="text-sm text-slate-400">No answers yet.</p>}
          </div>
        </div>
      )}

      {tab === 'questions' && (
        <div className="space-y-3">
          {userQuestions.length > 0
            ? userQuestions.map(q => <QuestionCard key={q.id} question={q} author={profileUser} />)
            : <div className="bg-white border border-slate-200 rounded-xl py-12 text-center text-slate-400 text-sm">No questions asked yet.</div>
          }
        </div>
      )}

      {tab === 'answers' && (
        <div className="space-y-3">
          {userAnswers.length > 0
            ? userAnswers.map(a => (
              <div key={a.id} className="bg-white border border-slate-200 rounded-xl p-5">
                <Link to={`/forum/${a.questionId}`} className="text-sm font-medium text-blue-700 hover:underline mb-2 block">View question →</Link>
                <p className="text-sm text-slate-700 line-clamp-3 leading-relaxed">{a.body}</p>
                <div className="flex items-center gap-3 mt-3 text-xs text-slate-400">
                  <span>{a.upvotes - a.downvotes} votes</span>
                  {a.isAccepted && <span className="text-green-600 font-medium">Accepted</span>}
                  <span>{formatRelativeDate(a.createdAt)}</span>
                </div>
              </div>
            ))
            : <div className="bg-white border border-slate-200 rounded-xl py-12 text-center text-slate-400 text-sm">No answers yet.</div>
          }
        </div>
      )}
    </div>
  );
}
