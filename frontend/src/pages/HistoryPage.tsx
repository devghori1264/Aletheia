/**
 * History Page
 *
 * List of past analyses with filtering and search.
 * Features:
 * - Theme-aware styling using Tailwind dark mode classes
 * - Responsive design for all screen sizes
 * - Client-side filtering by status
 * - Search by filename
 * - Pagination
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Shield,
  Clock,
  Trash2,
  MoreVertical,
  ChevronLeft,
  ChevronRight,
  FileVideo,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/Badge';
import { useAnalysisList, useDeleteAnalysis, useDebounce } from '@/hooks';
import { formatRelativeTime, cn } from '@/utils';
import type { AnalysisSummary } from '@/types/api';

// =============================================================================
// Types
// =============================================================================

type FilterStatus = 'all' | 'real' | 'fake' | 'pending';

// =============================================================================
// Filter Labels
// =============================================================================

const filterLabels: Record<FilterStatus, string> = {
  all: 'All',
  real: 'Authentic',
  fake: 'Suspicious',
  pending: 'Pending',
};

// =============================================================================
// Component
// =============================================================================

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');

  const debouncedSearch = useDebounce(searchQuery, 300);

  const { data, isLoading } = useAnalysisList({
    page,
    pageSize: 50, // Increase slightly so we can filter better locally across pages
  });

  const { mutate: deleteAnalysis, isPending: isDeleting } = useDeleteAnalysis();

  // Filter items client-side
  const filteredItems = useMemo(() => {
    if (!data?.items) return [];
    
    return data.items.filter((item) => {
      // Status filter
      if (filterStatus !== 'all') {
        const prediction = (item.prediction || '').toLowerCase();
        const status = (item.status || '').toLowerCase();
        
        if (filterStatus === 'pending') {
          // Both prediction unknown, or status is pending/processing
          if (prediction === 'real' || prediction === 'fake' || status === 'completed') {
            return false;
          }
        } else if (filterStatus === 'real' && prediction !== 'real') {
          return false;
        } else if (filterStatus === 'fake' && prediction !== 'fake') {
          return false;
        }
      }
      
      // Search filter
      if (debouncedSearch && !item.fileName.toLowerCase().includes(debouncedSearch.toLowerCase())) {
        return false;
      }
      
      return true;
    });
  }, [data?.items, filterStatus, debouncedSearch]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold sm:text-2xl text-neutral-900 dark:text-white">
            Analysis History
          </h1>
          <p className="mt-1 text-sm sm:text-base text-neutral-500 dark:text-neutral-400">
            View and manage your past deepfake analyses
          </p>
        </div>

        <Link to="/analyze" className="w-full sm:w-auto">
          <Button className="w-full sm:w-auto">New Analysis</Button>
        </Link>
      </div>

      {/* Filters */}
      <Card variant="glass" padding="sm">
        <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-neutral-400 dark:text-neutral-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by filename..."
              className="input-base !pl-11"
            />
          </div>

          {/* Status filter */}
          <div className="flex flex-wrap gap-2">
            {(['all', 'real', 'fake', 'pending'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={cn(
                  'rounded-lg px-3 py-2 text-sm font-medium transition-colors border',
                  filterStatus === status
                    ? 'bg-primary-500/10 text-primary-600 border-primary-500/20 dark:bg-primary-500/20 dark:text-primary-400'
                    : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 border-transparent dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white'
                )}
              >
                {filterLabels[status]}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Results */}
      <Card variant="default">
        {isLoading ? (
          <div className="space-y-3 p-4 sm:p-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="shimmer h-20 rounded-xl bg-neutral-100 dark:bg-neutral-800/50" />
            ))}
          </div>
        ) : filteredItems && filteredItems.length > 0 ? (
          <>
            <div className="divide-y divide-neutral-200 dark:divide-neutral-800/50">
              <AnimatePresence mode="popLayout">
                {filteredItems.map((analysis, index) => (
                  <AnalysisRow
                    key={analysis.id}
                    analysis={analysis}
                    index={index}
                    onDelete={() => deleteAnalysis(analysis.id)}
                    isDeleting={isDeleting}
                  />
                ))}
              </AnimatePresence>
            </div>

            {/* Pagination */}
            {data && data.meta.totalPages > 1 && (
              <div className="flex flex-col items-center justify-between gap-4 border-t p-4 sm:flex-row border-neutral-200 dark:border-neutral-800/50">
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                   Page {page} of {data.meta.totalPages}
                </p>

                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    <span className="hidden sm:inline">Previous</span>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={page === data.meta.totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    <span className="hidden sm:inline">Next</span>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="py-12 text-center sm:py-16">
            <Shield className="mx-auto h-12 w-12 text-neutral-400 dark:text-neutral-600" />
            <h3 className="mt-4 text-lg font-medium text-neutral-900 dark:text-white">
              No analyses found
            </h3>
            <p className="mt-2 text-neutral-500 dark:text-neutral-400">
               {searchQuery || filterStatus !== 'all'
                ? 'Try adjusting your filters'
                : 'Start by uploading a video or image'}
            </p>
            {!searchQuery && filterStatus === 'all' && (
              <Link to="/analyze" className="mt-6 inline-block">
                <Button>Start First Analysis</Button>
              </Link>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

// =============================================================================
// Analysis Row Component
// =============================================================================

function AnalysisRow({
  analysis,
  index,
  onDelete,
  isDeleting,
}: {
  analysis: AnalysisSummary;
  index: number;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -10 }}
      transition={{ delay: index * 0.03 }}
      className="group relative"
    >
      <Link
        to={`/results/${analysis.id}`}
        className="flex items-center gap-3 p-3 transition-colors sm:gap-4 sm:p-4 hover:bg-neutral-50 dark:hover:bg-neutral-800/30"
      >
        {/* Thumbnail */}
        <div className="h-12 w-12 flex-shrink-0 overflow-hidden rounded-xl sm:h-14 sm:w-14 bg-neutral-100 dark:bg-neutral-800">
           {analysis.thumbnailUrl ? (
            <img
              src={analysis.thumbnailUrl}
              alt=""
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              <FileVideo className="h-5 w-5 sm:h-6 sm:w-6 text-neutral-400 dark:text-neutral-600" />
            </div>
          )}
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium sm:text-base text-neutral-900 dark:text-white">
            {analysis.fileName}
          </p>
          <div className="mt-1 flex items-center gap-2 text-xs sm:text-sm text-neutral-500 dark:text-neutral-400">
             <Clock className="h-3.5 w-3.5" />
            {formatRelativeTime(analysis.createdAt)}
          </div>
        </div>

        {/* Confidence - hidden on mobile */}
        {analysis.confidence !== null && analysis.confidence !== undefined && (
          <div className="hidden text-right sm:block">
            <p className="text-sm text-neutral-500 dark:text-neutral-400">Confidence</p>
            <p className="font-semibold text-neutral-900 dark:text-white">
              {(analysis.confidence * 100).toFixed(1)}%
            </p>
          </div>
        )}

        {/* Status badge */}
        <StatusBadge status={analysis.prediction ?? 'pending'} />
      </Link>

      {/* Actions menu */}
      <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          onClick={(e) => {
            e.preventDefault();
            setShowMenu(!showMenu);
          }}
          className="flex h-8 w-8 items-center justify-center rounded-lg transition-colors text-neutral-400 hover:bg-neutral-200 hover:text-neutral-900 dark:hover:bg-neutral-700 dark:hover:text-white"
        >
          <MoreVertical className="h-4 w-4" />
        </button>

        <AnimatePresence>
          {showMenu && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="absolute right-0 top-full z-10 mt-1 w-40 overflow-hidden rounded-xl border shadow-xl border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-800"
            >
              <button
                onClick={(e) => {
                  e.preventDefault();
                  onDelete();
                  setShowMenu(false);
                }}
                disabled={isDeleting}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-danger-500 transition-colors hover:bg-danger-500/10 dark:text-danger-400"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
