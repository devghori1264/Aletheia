/**
 * Progress Component
 *
 * Animated progress bar with variants and value display.
 */

import { motion } from 'framer-motion';
import { cn } from '@/utils';

// =============================================================================
// Types
// =============================================================================

type ProgressVariant = 'default' | 'gradient' | 'success' | 'danger' | 'warning';
type ProgressSize = 'sm' | 'md' | 'lg';

interface ProgressProps {
  value: number;
  max?: number;
  variant?: ProgressVariant;
  size?: ProgressSize;
  showValue?: boolean;
  animated?: boolean;
  className?: string;
}

// =============================================================================
// Styles
// =============================================================================

const variantStyles: Record<ProgressVariant, string> = {
  default: 'bg-primary-500',
  gradient: 'bg-gradient-to-r from-primary-600 via-accent-500 to-primary-400',
  success: 'bg-success-500',
  danger: 'bg-danger-500',
  warning: 'bg-warning-500',
};

const sizeStyles: Record<ProgressSize, { bar: string; text: string }> = {
  sm: { bar: 'h-1.5', text: 'text-xs' },
  md: { bar: 'h-2.5', text: 'text-sm' },
  lg: { bar: 'h-4', text: 'text-base' },
};

// =============================================================================
// Component
// =============================================================================

export function Progress({
  value,
  max = 100,
  variant = 'default',
  size = 'md',
  showValue = false,
  animated = true,
  className,
}: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn('w-full', className)}>
      {/* Value display */}
      {showValue && (
        <div className={cn('mb-2 flex justify-between', sizeStyles[size].text)}>
          <span className="text-neutral-400">Progress</span>
          <span className="font-medium text-white">{percentage.toFixed(0)}%</span>
        </div>
      )}

      {/* Progress bar container */}
      <div
        className={cn(
          'w-full overflow-hidden rounded-full bg-neutral-800',
          sizeStyles[size].bar
        )}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        {/* Progress fill */}
        <motion.div
          initial={animated ? { width: 0 } : false}
          animate={{ width: `${percentage}%` }}
          transition={{
            duration: animated ? 0.5 : 0,
            ease: 'easeOut',
          }}
          className={cn(
            'h-full rounded-full',
            variantStyles[variant],
            animated && 'transition-all duration-500'
          )}
        >
          {/* Animated shine effect */}
          {animated && percentage > 0 && percentage < 100 && (
            <div className="h-full w-full animate-shimmer bg-gradient-shine bg-[length:200%_100%]" />
          )}
        </motion.div>
      </div>
    </div>
  );
}

// =============================================================================
// Circular Progress Component
// =============================================================================

interface CircularProgressProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  variant?: ProgressVariant;
  showValue?: boolean;
  className?: string;
}

export function CircularProgress({
  value,
  max = 100,
  size = 64,
  strokeWidth = 4,
  variant = 'default',
  showValue = true,
  className,
}: CircularProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  const colors: Record<ProgressVariant, string> = {
    default: '#0ea5e9',
    gradient: 'url(#gradient)',
    success: '#22c55e',
    danger: '#ef4444',
    warning: '#f59e0b',
  };

  return (
    <div className={cn('relative inline-flex', className)}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90 transform"
      >
        {/* Gradient definition */}
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#0284c7" />
            <stop offset="50%" stopColor="#d946ef" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
        </defs>

        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#262626"
          strokeWidth={strokeWidth}
        />

        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors[variant]}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </svg>

      {/* Center value */}
      {showValue && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-semibold text-white">
            {percentage.toFixed(0)}%
          </span>
        </div>
      )}
    </div>
  );
}
