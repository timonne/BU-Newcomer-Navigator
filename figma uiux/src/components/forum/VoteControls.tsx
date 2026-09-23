interface VoteControlsProps {
  upvotes: number;
  downvotes: number;
  userVote: 1 | -1 | 0;
  onVote: (value: 1 | -1) => void;
  disabled?: boolean;
  orientation?: 'vertical' | 'horizontal';
}

export default function VoteControls({ upvotes, downvotes, userVote, onVote, disabled, orientation = 'vertical' }: VoteControlsProps) {
  const net = upvotes - downvotes;
  const isVertical = orientation === 'vertical';
  const containerClass = isVertical ? 'flex flex-col items-center gap-1' : 'flex items-center gap-2';

  return (
    <div className={containerClass}>
      <button
        onClick={() => !disabled && onVote(1)}
        disabled={disabled}
        className={`p-1.5 rounded transition-colors ${
          userVote === 1
            ? 'text-blue-700 bg-blue-50'
            : 'text-slate-400 hover:text-blue-700 hover:bg-blue-50'
        } disabled:opacity-40 disabled:cursor-not-allowed`}
        aria-label="Upvote"
        title={disabled ? 'Sign in to vote' : 'Upvote'}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill={userVote === 1 ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 19V5M5 12l7-7 7 7" />
        </svg>
      </button>
      <span className={`font-semibold text-sm min-w-[1.5rem] text-center ${net > 0 ? 'text-blue-700' : net < 0 ? 'text-red-600' : 'text-slate-500'}`}>
        {net}
      </span>
      <button
        onClick={() => !disabled && onVote(-1)}
        disabled={disabled}
        className={`p-1.5 rounded transition-colors ${
          userVote === -1
            ? 'text-red-600 bg-red-50'
            : 'text-slate-400 hover:text-red-600 hover:bg-red-50'
        } disabled:opacity-40 disabled:cursor-not-allowed`}
        aria-label="Downvote"
        title={disabled ? 'Sign in to vote' : 'Downvote'}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill={userVote === -1 ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 5v14M19 12l-7 7-7-7" />
        </svg>
      </button>
    </div>
  );
}
