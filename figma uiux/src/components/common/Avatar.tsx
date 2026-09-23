import type { User } from '../../types';

interface AvatarProps {
  user: Pick<User, 'fullName' | 'avatarColor'>;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizes = {
  sm: 'w-7 h-7 text-xs',
  md: 'w-9 h-9 text-sm',
  lg: 'w-12 h-12 text-base',
  xl: 'w-20 h-20 text-2xl',
};

export default function Avatar({ user, size = 'md', className = '' }: AvatarProps) {
  const initials = user.fullName
    .split(' ')
    .slice(0, 2)
    .map(n => n[0])
    .join('')
    .toUpperCase();

  return (
    <div
      className={`${sizes[size]} rounded-full flex items-center justify-center font-semibold text-white flex-shrink-0 select-none ${className}`}
      style={{ backgroundColor: user.avatarColor }}
      aria-label={user.fullName}
    >
      {initials}
    </div>
  );
}
