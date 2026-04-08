/**
 * Layout Component
 *
 * Main application layout with navigation and content area.
 * Features:
 * - Collapsible sidebar (desktop toggle + mobile slide-out)
 * - Theme-aware styling using Tailwind dark mode classes
 * - Fully responsive design
 * - Privacy trust banner for user confidence
 */

import { useState, type ReactNode, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  Upload,
  History,
  Settings,
  Menu,
  Moon,
  Sun,
  Shield,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/utils';
import { useTheme } from '@/store';
import { useBreakpoint, useLocalStorage } from '@/hooks';
import { PrivacyBanner } from '@/components/ui/PrivacyBanner';
import logoUrl from '@/assets/logo.svg';

// =============================================================================
// Types
// =============================================================================

interface LayoutProps {
  children: ReactNode;
}

interface NavItem {
  path: string;
  label: string;
  icon: typeof Home;
}

// =============================================================================
// Navigation Items
// =============================================================================

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/analyze', label: 'Analyze', icon: Upload },
  { path: '/history', label: 'History', icon: History },
  { path: '/settings', label: 'Settings', icon: Settings },
];

// =============================================================================
// Layout Component
// =============================================================================

export function Layout({ children }: LayoutProps) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [desktopSidebarCollapsed, setDesktopSidebarCollapsed] = useLocalStorage('sidebar-collapsed', false);
  const { isMobile, isTablet, isDesktop } = useBreakpoint();
  const location = useLocation();
  const { resolvedTheme, toggleTheme } = useTheme();

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  // Determine sidebar state based on screen size
  const showSidebar = isMobile || isTablet ? mobileSidebarOpen : !desktopSidebarCollapsed;
  const sidebarWidth = desktopSidebarCollapsed ? 'w-20' : 'w-64';

  return (
    <div className="flex min-h-screen transition-colors duration-200 bg-neutral-50 dark:bg-neutral-950">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 transform backdrop-blur-xl transition-all duration-200',
          'bg-white/80 border-r border-neutral-200 shadow-lg dark:bg-neutral-900/50 dark:border-neutral-800/50',
          // Desktop behavior
          isDesktop && !desktopSidebarCollapsed && 'w-64 translate-x-0',
          isDesktop && desktopSidebarCollapsed && 'w-20 translate-x-0',
          // Mobile/Tablet behavior
          (isMobile || isTablet) && mobileSidebarOpen && 'w-64 translate-x-0',
          (isMobile || isTablet) && !mobileSidebarOpen && 'w-64 -translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <Link 
            to="/" 
            onClick={() => (isMobile || isTablet) && setMobileSidebarOpen(false)}
            className={cn(
              'flex h-16 items-center gap-3 border-b px-4 border-neutral-200 dark:border-neutral-800/50 transition-opacity hover:opacity-80 cursor-pointer',
              desktopSidebarCollapsed && isDesktop ? 'justify-center px-2' : 'px-6'
            )}
          >
            <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center ml-1">
              <img src={logoUrl} alt="Aletheia Logo" className="h-12 w-12 object-contain scale-125" />
            </div>
            <AnimatePresence>
              {(!desktopSidebarCollapsed || !isDesktop) && (
                <motion.div
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  className="overflow-hidden ml-2"
                >
                  <h1 className="font-display text-base font-semibold tracking-tight whitespace-nowrap text-neutral-900 dark:text-white">
                    Aletheia
                  </h1>
                  <p className="text-[10px] whitespace-nowrap text-neutral-500 dark:text-neutral-400">Deepfake Detection</p>
                </motion.div>
              )}
            </AnimatePresence>
          </Link>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileSidebarOpen(false)}
                  title={desktopSidebarCollapsed && isDesktop ? item.label : undefined}
                  className={cn(
                    'group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200',
                    desktopSidebarCollapsed && isDesktop && 'justify-center px-3',
                    isActive
                      ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                      : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800/50 dark:hover:text-white'
                  )}
                >
                  <Icon
                    className={cn(
                      'h-5 w-5 flex-shrink-0 transition-colors',
                      isActive 
                        ? 'text-primary-600 dark:text-primary-400'
                        : 'text-neutral-400 group-hover:text-neutral-900 dark:text-neutral-500 dark:group-hover:text-white'
                    )}
                  />
                  <AnimatePresence>
                    {(!desktopSidebarCollapsed || !isDesktop) && (
                      <motion.span
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: 'auto' }}
                        exit={{ opacity: 0, width: 0 }}
                        className="overflow-hidden whitespace-nowrap"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                  {isActive && (!desktopSidebarCollapsed || !isDesktop) && (
                    <motion.div
                      layoutId="activeNav"
                      className="ml-auto h-1.5 w-1.5 rounded-full bg-primary-400"
                    />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Bottom section */}
          <div className="border-t p-4 border-neutral-200 dark:border-neutral-800/50">
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              title={desktopSidebarCollapsed && isDesktop ? (resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode') : undefined}
              className={cn(
                'flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all',
                desktopSidebarCollapsed && isDesktop && 'justify-center px-3',
                'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800/50 dark:hover:text-white'
              )}
            >
              {resolvedTheme === 'dark' ? (
                <Sun className="h-5 w-5 flex-shrink-0" />
              ) : (
                <Moon className="h-5 w-5 flex-shrink-0" />
              )}
              <AnimatePresence>
                {(!desktopSidebarCollapsed || !isDesktop) && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="overflow-hidden whitespace-nowrap"
                  >
                    {resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                  </motion.span>
                )}
              </AnimatePresence>
            </button>

            {/* Version info */}
            <AnimatePresence>
              {(!desktopSidebarCollapsed || !isDesktop) && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 rounded-xl p-4 overflow-hidden bg-neutral-100 dark:bg-neutral-800/30"
                >
                  <div className="flex items-center gap-2 text-xs text-neutral-400 dark:text-neutral-500">
                    <Sparkles className="h-3.5 w-3.5 text-primary-400" />
                    <span>Version 1.0.0</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </aside>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {(isMobile || isTablet) && mobileSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className={cn(
        'flex flex-1 flex-col transition-all duration-200',
        isDesktop && !desktopSidebarCollapsed && 'lg:ml-64',
        isDesktop && desktopSidebarCollapsed && 'lg:ml-20'
      )}>
        {/* ═══════════════════════════════════════════════════════════════════
            PRIVACY TRUST BANNER
            Prominently displayed to establish immediate user trust.
            Positioned at the very top for maximum visibility.
            ═══════════════════════════════════════════════════════════════════ */}
        <PrivacyBanner variant="header" animate />
        
        {/* Header - Desktop toggle + Mobile menu */}
        <header className={cn(
          'sticky top-0 z-30 flex h-16 items-center justify-between border-b px-4 backdrop-blur-xl transition-colors duration-200',
          'border-neutral-200 bg-white/80 dark:border-neutral-800/50 dark:bg-neutral-950/80'
        )}>
          {/* Desktop sidebar toggle & Mobile Menu Toggle */}
          <button
            onClick={() => {
              if (isMobile || isTablet) {
                setMobileSidebarOpen(true);
              } else {
                setDesktopSidebarCollapsed(!desktopSidebarCollapsed);
              }
            }}
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-xl transition-colors',
              'text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white'
            )}
            title={desktopSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Mobile logo - only show on mobile/tablet */}
          {(isMobile || isTablet) && (
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center">
                <img src={logoUrl} alt="Aletheia Logo" className="h-10 w-10 object-contain scale-125" />
              </div>
              <span className="font-display text-base font-semibold text-neutral-900 dark:text-white ml-1">Aletheia</span>
            </div>
          )}

          {/* Theme toggle on mobile header */}
          {(isMobile || isTablet) ? (
            <button
              onClick={toggleTheme}
              className={cn(
                'flex h-10 w-10 items-center justify-center rounded-xl transition-colors',
                'text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white'
              )}
            >
              {resolvedTheme === 'dark' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>
          ) : (
            <div /> // Spacer for desktop
          )}
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 w-full max-w-full overflow-x-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
