/**
 * Layout Component
 *
 * Main application layout with navigation and content area.
 */

import { useState, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  Upload,
  History,
  Settings,
  Menu,
  X,
  Moon,
  Sun,
  Shield,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/utils';
import { useTheme } from '@/store';
import { useBreakpoint } from '@/hooks';

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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isMobile } = useBreakpoint();
  const location = useLocation();
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <div className="flex min-h-screen bg-neutral-950">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-neutral-900/50 backdrop-blur-xl',
          'border-r border-neutral-800/50 transition-transform duration-300 lg:translate-x-0',
          isMobile ? (sidebarOpen ? 'translate-x-0' : '-translate-x-full') : ''
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-3 border-b border-neutral-800/50 px-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-accent-500">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="font-display text-lg font-bold tracking-tight text-white">
                Aletheia
              </h1>
              <p className="text-2xs text-neutral-500">Deepfake Detection</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    'group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium',
                    'transition-all duration-200',
                    isActive
                      ? 'bg-primary-500/10 text-primary-400'
                      : 'text-neutral-400 hover:bg-neutral-800/50 hover:text-white'
                  )}
                >
                  <Icon
                    className={cn(
                      'h-5 w-5 transition-colors',
                      isActive ? 'text-primary-400' : 'text-neutral-500 group-hover:text-white'
                    )}
                  />
                  {item.label}
                  {isActive && (
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
          <div className="border-t border-neutral-800/50 p-4">
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-neutral-400 transition-all hover:bg-neutral-800/50 hover:text-white"
            >
              {resolvedTheme === 'dark' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
              {resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </button>

            {/* Version info */}
            <div className="mt-4 rounded-xl bg-neutral-800/30 p-4">
              <div className="flex items-center gap-2 text-xs text-neutral-500">
                <Sparkles className="h-3.5 w-3.5 text-primary-400" />
                <span>Version 1.0.0</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {isMobile && sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex flex-1 flex-col lg:ml-64">
        {/* Mobile Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-neutral-800/50 bg-neutral-950/80 px-4 backdrop-blur-xl lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-white"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-accent-500">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <span className="font-display font-bold text-white">Aletheia</span>
          </div>

          <button
            onClick={toggleTheme}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-white"
          >
            {resolvedTheme === 'dark' ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </button>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-8">
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
