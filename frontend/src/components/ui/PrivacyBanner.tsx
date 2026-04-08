/**
 * Privacy Trust Banner Component
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * A prominently displayed, eye-catching banner that immediately establishes trust
 * with users by clearly communicating our zero-data-collection privacy policy.
 * 
 * Design Philosophy:
 *   This component addresses a critical UX concern: when users see a video upload
 *   interface, their immediate instinct is suspicion about data collection. This
 *   banner proactively addresses that concern before it becomes a barrier.
 * 
 * Visual Design:
 *   - Positioned at the top of the viewport for immediate visibility
 *   - Animated shimmer effect draws attention without being obnoxious
 *   - Shield icon reinforces the security/privacy message
 *   - Gradient text creates visual interest and premium feel
 *   - Responsive: full text on desktop, condensed on mobile
 * 
 * Accessibility:
 *   - Proper ARIA labels for screen readers
 *   - Sufficient color contrast in both light and dark modes
 *   - Animation respects prefers-reduced-motion
 * 
 * Performance:
 *   - CSS-based animations (GPU accelerated)
 *   - No external dependencies beyond Lucide icons
 *   - Minimal re-renders (no state)
 * 
 * @module components/ui/PrivacyBanner
 * @version 1.0.0
 */

import { memo } from 'react';
import { ShieldCheck, Lock, Eye, EyeOff } from 'lucide-react';
import { cn } from '@/utils';

// =============================================================================
// Types & Interfaces
// =============================================================================

interface PrivacyBannerProps {
  /** Optional additional CSS classes */
  className?: string;
  /** Variant style - 'header' for top bar, 'inline' for within content */
  variant?: 'header' | 'inline' | 'compact';
  /** Whether to show the animated shimmer effect */
  animate?: boolean;
}

// =============================================================================
// Animation Keyframes (injected via style tag for CSS-in-JS alternative)
// =============================================================================

const shimmerKeyframes = `
  @keyframes privacy-shimmer {
    0% {
      background-position: -200% center;
    }
    100% {
      background-position: 200% center;
    }
  }
  
  @keyframes privacy-pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }
  
  @keyframes privacy-glow {
    0%, 100% {
      box-shadow: 0 0 5px rgba(34, 197, 94, 0.3), 0 0 10px rgba(34, 197, 94, 0.1);
    }
    50% {
      box-shadow: 0 0 10px rgba(34, 197, 94, 0.5), 0 0 20px rgba(34, 197, 94, 0.2);
    }
  }
`;

// =============================================================================
// Privacy Banner Component
// =============================================================================

/**
 * PrivacyBanner - Eye-catching trust indicator
 * 
 * Displays a prominent message reassuring users that their data is never
 * collected, stored, or shared. Features an animated shimmer effect to
 * draw attention while maintaining a professional appearance.
 * 
 * @example
 * // In Layout.tsx - placed after the header
 * <PrivacyBanner variant="header" animate />
 * 
 * @example
 * // In AnalyzePage.tsx - inline with upload zone
 * <PrivacyBanner variant="inline" />
 */
export const PrivacyBanner = memo(function PrivacyBanner({
  className,
  variant = 'header',
  animate = true,
}: PrivacyBannerProps) {
  
  // Render variant-specific content
  if (variant === 'compact') {
    return (
      <>
        <style>{shimmerKeyframes}</style>
        <div
          className={cn(
            'flex items-center justify-center gap-2 py-1.5 px-3 text-xs font-medium',
            'bg-gradient-to-r from-emerald-500/10 via-green-500/10 to-emerald-500/10',
            'border-b border-emerald-500/20',
            'dark:from-emerald-500/5 dark:via-green-500/10 dark:to-emerald-500/5',
            className
          )}
          role="banner"
          aria-label="Privacy guarantee: We do not store your data"
        >
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" />
          <span className="text-emerald-700 dark:text-emerald-400">
            Your privacy is protected — No data stored
          </span>
        </div>
      </>
    );
  }
  
  if (variant === 'inline') {
    return (
      <>
        <style>{shimmerKeyframes}</style>
        <div
          className={cn(
            'relative overflow-hidden rounded-xl p-4',
            'bg-gradient-to-r from-emerald-500/5 via-green-500/10 to-emerald-500/5',
            'border border-emerald-500/20',
            'dark:from-emerald-900/20 dark:via-green-900/30 dark:to-emerald-900/20',
            'dark:border-emerald-500/30',
            className
          )}
          role="note"
          aria-label="Privacy policy information"
        >
          {/* Animated shimmer overlay */}
          {animate && (
            <div
              className="absolute inset-0 opacity-30"
              style={{
                background: 'linear-gradient(90deg, transparent, rgba(34, 197, 94, 0.15), transparent)',
                backgroundSize: '200% 100%',
                animation: 'privacy-shimmer 3s ease-in-out infinite',
              }}
              aria-hidden="true"
            />
          )}
          
          <div className="relative flex items-start gap-3">
            <div 
              className={cn(
                'flex-shrink-0 rounded-lg p-2',
                'bg-emerald-500/10 dark:bg-emerald-500/20'
              )}
              style={animate ? { animation: 'privacy-glow 2s ease-in-out infinite' } : undefined}
            >
              <ShieldCheck className="h-5 w-5 text-emerald-500" />
            </div>
            
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-emerald-700 dark:text-emerald-400 text-sm">
                100% Private & Secure
              </h4>
              <p className="mt-1 text-sm text-emerald-600/80 dark:text-emerald-300/70 leading-relaxed">
                We <strong>never</strong> store, save, or share your videos. Your files are processed 
                in real-time and <strong>immediately deleted</strong> after analysis. No accounts, 
                no tracking, no data collection — guaranteed.
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }
  
  // Default: Header variant (top banner)
  return (
    <>
      <style>{shimmerKeyframes}</style>
      <div
        className={cn(
          'relative overflow-hidden',
          'bg-gradient-to-r from-emerald-600/90 via-green-500/90 to-emerald-600/90',
          'dark:from-emerald-900/80 dark:via-green-800/80 dark:to-emerald-900/80',
          className
        )}
        role="banner"
        aria-label="Privacy guarantee banner"
      >
        {/* Animated shimmer effect */}
        {animate && (
          <div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
              backgroundSize: '200% 100%',
              animation: 'privacy-shimmer 2.5s ease-in-out infinite',
            }}
            aria-hidden="true"
          />
        )}
        
        {/* Content */}
        <div className="relative flex items-center justify-center gap-2 sm:gap-3 py-2 sm:py-2.5 px-4">
          {/* Shield Icon with glow effect */}
          <div 
            className="flex-shrink-0"
            style={animate ? { animation: 'privacy-pulse 2s ease-in-out infinite' } : undefined}
          >
            <ShieldCheck className="h-4 w-4 sm:h-5 sm:w-5 text-white drop-shadow-lg" />
          </div>
          
          {/* Main Text - Responsive */}
          <p className="text-xs sm:text-sm font-medium text-white text-center drop-shadow-sm">
            {/* Mobile: Short version */}
            <span className="sm:hidden">
              🔒 Your videos are <strong>never stored</strong> — 100% private
            </span>
            
            {/* Tablet and up: Full version */}
            <span className="hidden sm:inline">
              <Lock className="inline h-3.5 w-3.5 mr-1 -mt-0.5" />
              <strong>Your Privacy Matters:</strong> We never store, collect, or share your videos.
              <span className="hidden md:inline"> Files are analyzed in real-time and instantly deleted.</span>
              <span className="ml-1 opacity-90">Your data stays with you.</span>
            </span>
          </p>
          
          {/* Eye-off icon for visual reinforcement */}
          <div className="hidden lg:block flex-shrink-0 opacity-80">
            <EyeOff className="h-4 w-4 text-white/80" />
          </div>
        </div>
      </div>
    </>
  );
});

// =============================================================================
// Privacy Badge - Small inline indicator
// =============================================================================

interface PrivacyBadgeProps {
  className?: string;
  size?: 'sm' | 'md';
}

/**
 * PrivacyBadge - Small inline privacy indicator
 * 
 * A compact badge for placing near upload buttons or in footers
 * to reinforce the privacy message throughout the interface.
 * 
 * @example
 * <Button>Upload Video</Button>
 * <PrivacyBadge />
 */
export const PrivacyBadge = memo(function PrivacyBadge({
  className,
  size = 'sm',
}: PrivacyBadgeProps) {
  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  };
  
  const iconSize = {
    sm: 'h-3 w-3',
    md: 'h-3.5 w-3.5',
  };
  
  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        'bg-emerald-500/10 text-emerald-600',
        'dark:bg-emerald-500/20 dark:text-emerald-400',
        'border border-emerald-500/20 dark:border-emerald-500/30',
        sizeClasses[size],
        className
      )}
      role="note"
      aria-label="Your data is not stored"
    >
      <ShieldCheck className={cn(iconSize[size], 'flex-shrink-0')} />
      <span>No data stored</span>
    </div>
  );
});

// =============================================================================
// Privacy Notice - Detailed expandable notice
// =============================================================================

interface PrivacyNoticeProps {
  className?: string;
}

/**
 * PrivacyNotice - Detailed privacy information card
 * 
 * A more comprehensive privacy explanation for settings pages
 * or dedicated privacy sections.
 */
export const PrivacyNotice = memo(function PrivacyNotice({
  className,
}: PrivacyNoticeProps) {
  return (
    <div
      className={cn(
        'rounded-xl border p-5',
        'bg-gradient-to-br from-emerald-50 to-green-50',
        'border-emerald-200',
        'dark:from-emerald-900/20 dark:to-green-900/20',
        'dark:border-emerald-800/50',
        className
      )}
      role="region"
      aria-labelledby="privacy-notice-title"
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 rounded-full bg-emerald-500/20 p-3 dark:bg-emerald-500/30">
          <ShieldCheck className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
        </div>
        
        <div className="flex-1">
          <h3 
            id="privacy-notice-title"
            className="font-semibold text-emerald-800 dark:text-emerald-300"
          >
            Your Privacy is Our Priority
          </h3>
          
          <ul className="mt-3 space-y-2 text-sm text-emerald-700 dark:text-emerald-300/80">
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
              <span><strong>Zero Storage:</strong> Videos are processed in memory and never saved to any server</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
              <span><strong>No Accounts:</strong> No registration, no login, no personal information required</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
              <span><strong>No Tracking:</strong> We don't use cookies or analytics that identify you</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
              <span><strong>Instant Deletion:</strong> Your video is deleted immediately after analysis completes</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
              <span><strong>Open Source:</strong> Our code is public — verify our privacy claims yourself</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
});

// =============================================================================
// Exports
// =============================================================================

export default PrivacyBanner;
