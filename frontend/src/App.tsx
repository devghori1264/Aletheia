import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';

import { Layout } from '@/components/layout/Layout';
import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

// Lazy-loaded pages for code splitting
const HomePage = lazy(() => import('@/pages/HomePage'));
const AnalyzePage = lazy(() => import('@/pages/AnalyzePage'));
const ResultsPage = lazy(() => import('@/pages/ResultsPage'));
const HistoryPage = lazy(() => import('@/pages/HistoryPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

/**
 * Main application component.
 * 
 * Features:
 * - Lazy-loaded routes for optimal performance
 * - Error boundaries for graceful error handling
 * - Suspense for loading states
 * - Protected route support (future)
 */
export default function App() {
  return (
    <ErrorBoundary>
      <Layout>
        <Suspense fallback={<LoadingScreen />}>
          <Routes>
            {/* Main routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/results/:id" element={<ResultsPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            
            {/* Redirect old routes */}
            <Route path="/upload" element={<Navigate to="/analyze" replace />} />
            <Route path="/analysis/:id" element={<Navigate to="/results/:id" replace />} />
            
            {/* 404 */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </Layout>
    </ErrorBoundary>
  );
}
