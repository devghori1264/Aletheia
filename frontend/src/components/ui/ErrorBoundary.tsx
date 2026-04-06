/**
 * Error Boundary Component
 *
 * Catches JavaScript errors in child component tree and displays fallback UI.
 */

import { Component, type ReactNode, type ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Link } from 'react-router-dom';

// =============================================================================
// Types
// =============================================================================

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

// =============================================================================
// Error Boundary Component
// =============================================================================

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Error caught by boundary:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center p-8 lg:h-screen">
          <div className="max-w-md text-center">
            {/* Error Icon */}
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-danger-500/10">
              <AlertTriangle className="h-8 w-8 text-danger-500" />
            </div>

            {/* Error Message */}
            <h1 className="mt-6 text-2xl font-bold text-white">Something went wrong</h1>
            <p className="mt-2 text-neutral-400">
              An unexpected error occurred. Please try again or return to the home page.
            </p>

            {/* Error Details (Development) */}
            {import.meta.env.DEV && this.state.error && (
              <div className="mt-4 rounded-xl bg-neutral-800/50 p-4 text-left">
                <p className="font-mono text-xs text-danger-400">{this.state.error.message}</p>
              </div>
            )}

            {/* Actions */}
            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
              <button
                onClick={this.handleReset}
                className="btn-primary inline-flex items-center justify-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Try Again
              </button>

              <Link
                to="/"
                onClick={this.handleReset}
                className="btn-secondary inline-flex items-center justify-center gap-2"
              >
                <Home className="h-4 w-4" />
                Go Home
              </Link>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
