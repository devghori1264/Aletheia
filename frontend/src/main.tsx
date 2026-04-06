import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import App from './App';
import { ThemeProvider } from './store/theme-context';
import './styles/globals.css';

/**
 * React Query client configuration.
 * 
 * Optimized for real-time analysis workflows:
 * - Aggressive refetch for analysis status
 * - Longer stale time for static data
 * - Error retry with exponential backoff
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes (previously cacheTime)
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && 'status' in error) {
          const status = (error as Error & { status: number }).status;
          if (status >= 400 && status < 500) return false;
        }
        return failureCount < 3;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});

/**
 * Application root.
 * 
 * Provider hierarchy:
 * 1. StrictMode - Development checks
 * 2. QueryClientProvider - Server state management
 * 3. BrowserRouter - Client-side routing
 * 4. ThemeProvider - Theme context
 */
const container = document.getElementById('root');

if (!container) {
  throw new Error('Root element not found. Ensure index.html has <div id="root"></div>');
}

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <ThemeProvider>
          <App />
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              className: '!bg-neutral-800 !text-neutral-100 !border !border-neutral-700',
              success: {
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#171717',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#171717',
                },
              },
            }}
          />
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
);
