/**
 * Results Page
 *
 * Display analysis results with detailed breakdown.
 */

import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Download,
  Share2,
  RefreshCw,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { ResultDisplay } from '@/components/analysis/ResultDisplay';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/Progress';
import { Badge } from '@/components/ui/Badge';
import { useAnalysis } from '@/hooks';

// =============================================================================
// Component
// =============================================================================

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: analysis, isLoading, error, refetch } = useAnalysis(id);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary-400" />
          <p className="mt-4 text-neutral-400">Loading analysis...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !analysis) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Card variant="glass" className="max-w-md p-8 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-danger-400" />
          <h2 className="mt-4 text-xl font-semibold text-white">Analysis Not Found</h2>
          <p className="mt-2 text-neutral-400">
            The analysis you're looking for doesn't exist or has been deleted.
          </p>
          <Link to="/analyze" className="mt-6 inline-block">
            <Button>Start New Analysis</Button>
          </Link>
        </Card>
      </div>
    );
  }

  // Processing state
  if (analysis.status === 'pending' || analysis.status === 'processing') {
    return (
      <div className="mx-auto max-w-2xl space-y-8">
        {/* Back button */}
        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-neutral-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to history
        </Link>

        {/* Processing card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card variant="glass" padding="lg" className="text-center">
            {/* Animated icon */}
            <motion.div
              animate={{
                scale: [1, 1.1, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-primary-500/20"
            >
              <Loader2 className="h-10 w-10 animate-spin text-primary-400" />
            </motion.div>

            <h2 className="mt-6 text-2xl font-bold text-white">
              {analysis.status === 'pending' ? 'Queued for Processing' : 'Analyzing Media'}
            </h2>

            <p className="mt-2 text-neutral-400">
              {analysis.status === 'pending'
                ? 'Your analysis is in queue and will start shortly.'
                : 'Our AI models are analyzing your media for signs of manipulation.'}
            </p>

            {/* Progress bar */}
            <div className="mx-auto mt-8 max-w-sm">
              <Progress value={analysis.progress} variant="gradient" showValue />
            </div>

            {/* Stage info */}
            <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
              <Badge variant="primary">
                {analysis.progress < 25
                  ? 'Extracting frames'
                  : analysis.progress < 50
                    ? 'Detecting faces'
                    : analysis.progress < 75
                      ? 'Running models'
                      : 'Finalizing results'}
              </Badge>
            </div>

            {/* File info */}
            <div className="mt-8 rounded-xl bg-neutral-800/30 p-4">
              <p className="text-sm text-neutral-400">
                <strong className="text-white">File:</strong> {analysis.mediaFile?.fileName || 'Uploaded file'}
              </p>
            </div>
          </Card>
        </motion.div>
      </div>
    );
  }

  // Failed state
  if (analysis.status === 'failed') {
    return (
      <div className="mx-auto max-w-2xl space-y-8">
        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-neutral-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to history
        </Link>

        <Card variant="glass" padding="lg" className="text-center">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-danger-500/20">
            <AlertCircle className="h-10 w-10 text-danger-400" />
          </div>

          <h2 className="mt-6 text-2xl font-bold text-white">Analysis Failed</h2>

          <p className="mt-2 text-neutral-400">
            {analysis.errorMessage || 'An unexpected error occurred during analysis.'}
          </p>

          <div className="mt-8 flex justify-center gap-4">
            <Button variant="secondary" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
              Retry Analysis
            </Button>
            <Link to="/analyze">
              <Button>Upload New File</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Completed state
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-neutral-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to history
        </Link>

        <div className="flex gap-3">
          <Button variant="ghost" size="sm">
            <Share2 className="h-4 w-4" />
            Share
          </Button>
          <Button variant="secondary" size="sm">
            <Download className="h-4 w-4" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Results */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <ResultDisplay analysis={analysis} />
      </motion.div>

      {/* Media Preview */}
      {analysis.mediaFile && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card variant="default">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-white">Source Media</h3>
              <p className="mt-1 text-sm text-neutral-400">{analysis.mediaFile.fileName}</p>
            </div>

            <div className="aspect-video bg-neutral-800">
              {/* Video/image preview would go here */}
              <div className="flex h-full items-center justify-center text-neutral-500">
                Media preview
              </div>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
