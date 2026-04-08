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
  success: 'bg-success-100 text-success-700 border-success-200 dark:bg-success-500/10 dark:text-success-400 dark:border-success-500/20',
  danger: 'bg-danger-100 text-danger-700 border-danger-200 dark:bg-danger-500/10 dark:text-danger-400 dark:border-danger-500/20',
  warning: 'bg-warning-100 text-warning-700 border-warning-200 dark:bg-warning-500/10 dark:text-warning-400 dark:border-warning-500/20',
  neutral: 'bg-neutral-100 text-neutral-600 border-neutral-200 dark:bg-neutral-700/50 dark:text-neutral-300 dark:border-neutral-600/50',
  primary: 'bg-primary-100 text-primary-700 border-primary-200 dark:bg-primary-500/10 dark:text-primary-400 dark:border-primary-500/20',
  accent: 'bg-accent-100 text-accent-700 border-accent-200 dark:bg-accent-500/10 dark:text-accent-400 dark:border-accent-500/20',
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
