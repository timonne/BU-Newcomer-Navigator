import { Link } from 'react-router';
import type { Answer, User } from '../../types';
import Avatar from '../common/Avatar';
import VoteControls from './VoteControls';
import { formatRelativeDate } from '../../utils/date';

interface AnswerCardProps {
  answer: Answer;
  author: User | undefined;
  userVote: 1 | -1 | 0;
  onVote: (value: 1 | -1) => void;
  canVote: boolean;
}

export default function AnswerCard({ answer, author, userVote, onVote, canVote }: AnswerCardProps) {
  function renderMarkdown(text: string) {
    // Simple inline bold/code rendering without a dependency
    return text.split('\n').map((line, i) => {
      const parts = line.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, j) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={j}>{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return <code key={j} className="bg-slate-100 text-slate-700 px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
        }
        return <span key={j}>{part}</span>;
      });
      return <p key={i} className={`${i > 0 ? 'mt-2' : ''}`}>{parts}</p>;
    });
  }

  return (
    <div className={`bg-white border rounded-xl p-5 ${answer.isAccepted ? 'border-green-300 bg-green-50/30' : 'border-slate-200'}`}>
      {answer.isAccepted && (
        <div className="flex items-center gap-1.5 text-green-700 text-xs font-semibold mb-3">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 8l3.5 3.5 6.5-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Accepted Answer
        </div>
      )}

      <div className="flex gap-4">
        <VoteControls
          upvotes={answer.upvotes}
          downvotes={answer.downvotes}
          userVote={userVote}
          onVote={onVote}
          disabled={!canVote}
        />

        <div className="flex-1 min-w-0">
          <div className="text-sm text-slate-700 leading-relaxed space-y-1">
            {renderMarkdown(answer.body)}
          </div>

          {author && (
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-100">
              <Link to={`/profile/${author.id}`} className="flex items-center gap-2 text-xs text-slate-500 hover:text-blue-700 transition-colors">
                <Avatar user={author} size="sm" />
                <span className="font-medium">{author.fullName}</span>
                {author.verificationStatus === 'verified' && (
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="none" className="text-blue-600">
                    <circle cx="8" cy="8" r="7" fill="currentColor" fillOpacity="0.15"/>
                    <path d="M5 8l2.5 2.5L11 5.5" stroke="#1E3A8A" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </Link>
              <span className="text-xs text-slate-300">·</span>
              <span className="text-xs text-slate-400">{formatRelativeDate(answer.createdAt)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
