import { Link } from 'react-router';
import type { Question, User } from '../../types';
import Avatar from '../common/Avatar';
import Badge from '../common/Badge';
import { getCategoryById, getTagById } from '../../data/categories';
import { formatRelativeDate } from '../../utils/date';

interface QuestionCardProps {
  question: Question;
  author: User | undefined;
}

export default function QuestionCard({ question, author }: QuestionCardProps) {
  const category = getCategoryById(question.categoryId);
  const net = question.upvotes - question.downvotes;

  return (
    <article className="bg-white border border-slate-200 rounded-xl p-5 hover:border-blue-200 hover:shadow-sm transition-all group">
      <div className="flex gap-4">
        {/* Vote count */}
        <div className="flex flex-col items-center gap-1 flex-shrink-0 pt-0.5">
          <span className={`text-lg font-bold ${net > 0 ? 'text-blue-700' : 'text-slate-400'}`}>{net}</span>
          <span className="text-[10px] text-slate-400 leading-none">votes</span>
        </div>

        {/* Answer / view stats */}
        <div className="flex flex-col items-center gap-1 flex-shrink-0 pt-0.5">
          <span
            className={`text-lg font-bold ${
              question.isAnswered ? 'text-green-700' : 'text-slate-400'
            }`}
          >
            {question.answerCount}
          </span>
          <span className="text-[10px] text-slate-400 leading-none">
            {question.isAnswered ? 'answers' : 'answers'}
          </span>
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-start gap-2 mb-2">
            {question.isAnswered && (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
                <svg width="10" height="10" viewBox="0 0 16 16" fill="none"><path d="M3 8l3.5 3.5 6.5-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                Answered
              </span>
            )}
            {category && (
              <Badge label={category.name} color="#1E3A8A" variant="soft" />
            )}
          </div>

          <Link
            to={`/forum/${question.id}`}
            className="block text-base font-semibold text-slate-800 group-hover:text-blue-800 transition-colors mb-2 leading-snug"
          >
            {question.title}
          </Link>

          <p className="text-sm text-slate-500 line-clamp-2 mb-3 leading-relaxed">
            {question.body.substring(0, 200).replace(/\n/g, ' ')}…
          </p>

          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-1.5">
              {question.tags.slice(0, 3).map(tagId => {
                const tag = getTagById(tagId);
                return tag ? <Badge key={tagId} label={tag.name} color={tag.color} variant="outline" /> : null;
              })}
            </div>
            {author && (
              <div className="flex items-center gap-2 flex-shrink-0">
                <Link to={`/profile/${author.id}`} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-blue-700 transition-colors">
                  <Avatar user={author} size="sm" />
                  <span>{author.username}</span>
                </Link>
                <span className="text-xs text-slate-400">·</span>
                <span className="text-xs text-slate-400">{formatRelativeDate(question.createdAt)}</span>
                <span className="text-xs text-slate-400">·</span>
                <span className="text-xs text-slate-400">{question.views} views</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
