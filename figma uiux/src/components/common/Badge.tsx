interface BadgeProps {
  label: string;
  color?: string;
  variant?: 'solid' | 'outline' | 'soft';
  size?: 'sm' | 'md';
  className?: string;
}

export default function Badge({ label, color = '#1E3A8A', variant = 'soft', size = 'sm', className = '' }: BadgeProps) {
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  if (variant === 'solid') {
    return (
      <span
        className={`inline-flex items-center rounded font-medium ${padding} ${className}`}
        style={{ backgroundColor: color, color: '#fff' }}
      >
        {label}
      </span>
    );
  }

  if (variant === 'outline') {
    return (
      <span
        className={`inline-flex items-center rounded font-medium ${padding} bg-transparent border ${className}`}
        style={{ borderColor: color, color }}
      >
        {label}
      </span>
    );
  }

  // soft
  return (
    <span
      className={`inline-flex items-center rounded font-medium ${padding} ${className}`}
      style={{ backgroundColor: `${color}18`, color }}
    >
      {label}
    </span>
  );
}
