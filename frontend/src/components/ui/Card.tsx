/**
 * Card Component
 *
 * Versatile card container with glass morphism variants.
 */

import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/utils';

// =============================================================================
// Types
// =============================================================================

type CardVariant = 'default' | 'glass' | 'elevated' | 'outlined';
type CardPadding = 'none' | 'sm' | 'md' | 'lg';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  padding?: CardPadding;
  hoverable?: boolean;
  clickable?: boolean;
}

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
  action?: ReactNode;
}

// =============================================================================
// Styles
// =============================================================================

const variantStyles: Record<CardVariant, string> = {
  default: 'bg-neutral-900/50 border border-neutral-800/50',
  glass: cn(
    'bg-white/[0.02] backdrop-blur-xl border border-white/5',
    'before:absolute before:inset-0 before:bg-gradient-to-br before:from-white/[0.08] before:to-transparent before:pointer-events-none before:rounded-inherit'
  ),
  elevated: 'bg-neutral-900 shadow-xl shadow-black/20 border border-neutral-800/30',
  outlined: 'bg-transparent border border-neutral-700',
};

const paddingStyles: Record<CardPadding, string> = {
  none: 'p-0',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

// =============================================================================
// Card Component
// =============================================================================

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = 'default',
      padding = 'md',
      hoverable = false,
      clickable = false,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          'relative overflow-hidden rounded-2xl',
          variantStyles[variant],
          paddingStyles[padding],
          hoverable && 'transition-all duration-300 hover:-translate-y-1 hover:shadow-lg',
          clickable && 'cursor-pointer',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// =============================================================================
// Card Header Component
// =============================================================================

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, title, description, action, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex items-start justify-between gap-4', className)}
        {...props}
      >
        <div className="flex-1">
          {title && (
            <h3 className="text-lg font-semibold text-white">{title}</h3>
          )}
          {description && (
            <p className="mt-1 text-sm text-neutral-400">{description}</p>
          )}
          {children}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

// =============================================================================
// Card Content Component
// =============================================================================

export const CardContent = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
  return <div ref={ref} className={cn('mt-4', className)} {...props} />;
});

CardContent.displayName = 'CardContent';

// =============================================================================
// Card Footer Component
// =============================================================================

export const CardFooter = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        'mt-6 flex items-center justify-end gap-3 border-t border-neutral-800/50 pt-4',
        className
      )}
      {...props}
    />
  );
});

CardFooter.displayName = 'CardFooter';
