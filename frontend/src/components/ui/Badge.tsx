/**
 * Badge Component
 *
 * Small label for status, categories, and counts.
 */

import { forwardRef, type HTMLAttributes } from 'react';
import { cn } from '@/utils';

// =============================================================================
// Types
// =============================================================================

type BadgeVariant = 'success' | 'danger' | 'warning' | 'neutral' | 'primary' | 'accent';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
}

// =============================================================================
// Styles
// =============================================================================

const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-success-500/10 text-success-400 border-success-500/20',
  danger: 'bg-danger-500/10 text-danger-400 border-danger-500/20',
  warning: 'bg-warning-500/10 text-warning-400 border-warning-500/20',
  neutral: 'bg-neutral-700/50 text-neutral-300 border-neutral-600/50',
  primary: 'bg-primary-500/10 text-primary-400 border-primary-500/20',
  accent: 'bg-accent-500/10 text-accent-400 border-accent-500/20',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-2xs',
  md: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
};

const dotStyles: Record<BadgeVariant, string> = {
  success: 'bg-success-500',
  danger: 'bg-danger-500',
  warning: 'bg-warning-500',
  neutral: 'bg-neutral-500',
  primary: 'bg-primary-500',
  accent: 'bg-accent-500',
};

// =============================================================================
// Component
// =============================================================================

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'neutral', size = 'md', dot = false, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full border font-medium',
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={cn(
              'h-1.5 w-1.5 rounded-full',
              dotStyles[variant],
              variant !== 'neutral' && 'animate-pulse'
            )}
          />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

// =============================================================================
// Preset Badges
// =============================================================================

export function StatusBadge({ status }: { status: 'real' | 'fake' | 'uncertain' | 'pending' }) {
  const config: Record<typeof status, { variant: BadgeVariant; label: string }> = {
    real: { variant: 'success', label: 'Authentic' },
    fake: { variant: 'danger', label: 'Manipulated' },
    uncertain: { variant: 'warning', label: 'Uncertain' },
    pending: { variant: 'neutral', label: 'Pending' },
  };

  const { variant, label } = config[status];

  return (
    <Badge variant={variant} dot>
      {label}
    </Badge>
  );
}

export function ConfidenceBadge({ confidence }: { confidence: number }) {
  // Auto-detect range: if > 1, assume 0-100 range; otherwise 0-1 range
  const percent = confidence > 1 ? confidence : confidence * 100;

  let variant: BadgeVariant;
  let label: string;

  if (percent >= 95) {
    variant = 'success';
    label = 'Very High';
  } else if (percent >= 85) {
    variant = 'primary';
    label = 'High';
  } else if (percent >= 70) {
    variant = 'warning';
    label = 'Medium';
  } else {
    variant = 'neutral';
    label = 'Low';
  }

  return (
    <Badge variant={variant} size="sm">
      {label} ({percent.toFixed(0)}%)
    </Badge>
  );
}
