/**
 * Button Component
 *
 * Reusable button with variants, sizes, and loading states.
 */

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils';

// =============================================================================
// Types
// =============================================================================

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'link';
type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

// =============================================================================
// Styles
// =============================================================================

const variantStyles: Record<ButtonVariant, string> = {
  primary: cn(
    'bg-primary-600 text-white',
    'hover:bg-primary-500 hover:shadow-glow-sm',
    'focus:ring-primary-500',
    'disabled:hover:bg-primary-600 disabled:hover:shadow-none'
  ),
  secondary: cn(
    'bg-neutral-800 text-neutral-100 border border-neutral-700',
    'hover:bg-neutral-700 hover:border-neutral-600',
    'focus:ring-neutral-500'
  ),
  ghost: cn(
    'text-neutral-300',
    'hover:bg-neutral-800 hover:text-neutral-100',
    'focus:ring-neutral-500'
  ),
  danger: cn(
    'bg-danger-600 text-white',
    'hover:bg-danger-500 hover:shadow-glow-danger',
    'focus:ring-danger-500'
  ),
  link: cn(
    'text-primary-400 underline-offset-4',
    'hover:text-primary-300 hover:underline',
    'focus:ring-primary-500'
  ),
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs gap-1.5 rounded-lg',
  md: 'h-10 px-4 text-sm gap-2 rounded-xl',
  lg: 'h-12 px-6 text-base gap-2 rounded-xl',
  xl: 'h-14 px-8 text-lg gap-3 rounded-2xl',
};

const iconSizeStyles: Record<ButtonSize, string> = {
  sm: 'h-3.5 w-3.5',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
  xl: 'h-6 w-6',
};

// =============================================================================
// Component
// =============================================================================

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center font-medium',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-950',
          'disabled:opacity-50 disabled:cursor-not-allowed',

          // Variant styles
          variantStyles[variant],

          // Size styles
          sizeStyles[size],

          // Full width
          fullWidth && 'w-full',

          className
        )}
        {...props}
      >
        {/* Loading spinner */}
        {isLoading && (
          <Loader2 className={cn('animate-spin', iconSizeStyles[size])} />
        )}

        {/* Left icon */}
        {!isLoading && leftIcon && (
          <span className={iconSizeStyles[size]}>{leftIcon}</span>
        )}

        {/* Children */}
        {children}

        {/* Right icon */}
        {!isLoading && rightIcon && (
          <span className={iconSizeStyles[size]}>{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
