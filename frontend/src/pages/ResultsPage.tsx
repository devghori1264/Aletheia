/**
 * Results Page
 *
 * Display analysis results with detailed breakdown.
 * Features:
 * - Video preview player for completed analyses
 * - Processing state with animated progress
 * - Theme-aware styling using Tailwind dark mode classes
 * - Responsive layout
 * - Privacy assurance messaging
 */

import { useParams, Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Download,
  Share2,
  RefreshCw,
  Loader2,
  AlertCircle,
  Play,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { ResultDisplay } from '@/components/analysis/ResultDisplay';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/Progress';
import { Badge } from '@/components/ui/Badge';
import { PrivacyBadge } from '@/components/ui/PrivacyBanner';
import { useAnalysis } from '@/hooks';
import { cn } from '@/utils';

// =============================================================================
// Helper: Get video URL from analysis
// =============================================================================

function getVideoUrl(analysis: { mediaFile?: { id?: string; fileName?: string; fileUrl?: string | null } } | null): string | null {
  // Use the fileUrl from the backend if available
  if (analysis?.mediaFile?.fileUrl) {
    return analysis.mediaFile.fileUrl;
  }

  // Fallback: construct URL (shouldn't be needed with backend fix)
  if (!analysis?.mediaFile?.fileName) return null;
  return null;
}

interface ResultsRouteState {
  localPreviewUrl?: string;
  localFileName?: string;
}

// =============================================================================
// Video Player Component
// =============================================================================

function VideoPlayer({ src, fileName }: { src: string; fileName: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [hasError, setHasError] = useState(false);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  if (hasError) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-neutral-500 dark:text-neutral-400">
        <AlertCircle className="mb-4 h-12 w-12 opacity-50" />
        <p className="text-center">Unable to load video preview</p>
        <p className="mt-1 text-sm opacity-75">{fileName}</p>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full group">
      <video
        ref={videoRef}
        src={src}
        className="h-full w-full object-contain"
        muted={isMuted}
        playsInline
        loop
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onError={() => setHasError(true)}
      />

      {/* Video Controls Overlay */}
      <div className={cn(
        'absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100',
        !isPlaying && 'opacity-100'
      )}>
        <button
          onClick={togglePlay}
          className="flex h-16 w-16 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm transition-transform hover:scale-110"
        >
          {isPlaying ? (
            <div className="flex gap-1">
              <div className="h-6 w-2 rounded bg-white" />
              <div className="h-6 w-2 rounded bg-white" />
            </div>
          ) : (
            <Play className="h-8 w-8 text-white ml-1" fill="white" />
          )}
        </button>
      </div>

      {/* Mute button */}
      <button
        onClick={toggleMute}
        className="absolute bottom-4 right-4 flex h-10 w-10 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition-opacity opacity-0 group-hover:opacity-100"
      >
        {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
      </button>
    </div>
  );
}

// =============================================================================
// Component
// =============================================================================

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const routeState = (location.state as ResultsRouteState | null) ?? null;
  const localPreviewUrl = routeState?.localPreviewUrl ?? null;
  const { data: analysis, isLoading, error, refetch } = useAnalysis(id);

  // Cleanup local object URL when leaving the page.
  useEffect(() => {
    if (!localPreviewUrl || !localPreviewUrl.startsWith('blob:')) return;

    return () => {
      URL.revokeObjectURL(localPreviewUrl);
    };
  }, [localPreviewUrl]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary-400" />
          <p className="mt-4 text-neutral-500 dark:text-neutral-400">Loading analysis...</p>
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
          <h2 className="mt-4 text-xl font-semibold text-neutral-900 dark:text-white">Analysis Not Found</h2>
          <p className="mt-2 text-neutral-500 dark:text-neutral-400">
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
      <div className="mx-auto max-w-2xl space-y-8 px-4">
        {/* Back button */}
        <Link
          to="/history"
          className="inline-flex items-center gap-2 transition-colors text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
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
              className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-primary-500/10 dark:bg-primary-500/20"
            >
              <Loader2 className="h-10 w-10 animate-spin text-primary-500 dark:text-primary-400" />
            </motion.div>

            <h2 className="mt-6 text-xl font-bold sm:text-2xl text-neutral-900 dark:text-white">
              {analysis.status === 'pending' ? 'Queued for Processing' : 'Analyzing Media'}
            </h2>

            <p className="mt-2 text-neutral-500 dark:text-neutral-400">
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
            <div className="mt-8 rounded-xl p-4 bg-neutral-100 dark:bg-neutral-800/30">
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                <strong className="text-neutral-900 dark:text-white">
                  File:
                </strong>{' '}
                {analysis.mediaFile?.fileName || 'Uploaded file'}
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
      <div className="mx-auto max-w-2xl space-y-8 px-4">
        <Link
          to="/history"
          className="inline-flex items-center gap-2 transition-colors text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to history
        </Link>

        <Card variant="glass" padding="lg" className="text-center">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-danger-500/10 dark:bg-danger-500/20">
            <AlertCircle className="h-10 w-10 text-danger-500 dark:text-danger-400" />
          </div>

          <h2 className="mt-6 text-xl font-bold sm:text-2xl text-neutral-900 dark:text-white">Analysis Failed</h2>

          <p className="mt-2 text-neutral-500 dark:text-neutral-400">
            {analysis.errorMessage || 'An unexpected error occurred during analysis.'}
          </p>

          <div className="mt-8 flex flex-col justify-center gap-4 sm:flex-row">
            <Button variant="secondary" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
              Retry Analysis
            </Button>
            <Link to="/analyze">
              <Button className="w-full sm:w-auto">Upload New File</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Get video URL for preview
  const videoUrl = localPreviewUrl || getVideoUrl(analysis);

  // Completed state
  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <Link
          to="/history"
          className="inline-flex items-center gap-2 transition-colors text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to history
        </Link>

        <div className="flex gap-3">
          <Button variant="ghost" size="sm">
            <Share2 className="h-4 w-4" />
            <span className="hidden sm:inline">Share</span>
          </Button>
          <Button variant="secondary" size="sm">
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Export Report</span>
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
            <div className="p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-white">Source Media</h3>
              <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
                {routeState?.localFileName || analysis.mediaFile.fileName}
              </p>
            </div>

            <div className="aspect-video bg-neutral-100 dark:bg-neutral-800 relative">
              {videoUrl ? (
                <VideoPlayer
                  src={videoUrl}
                  fileName={routeState?.localFileName || analysis.mediaFile.fileName}
                />
              ) : (
                <div className="flex h-full items-center justify-center text-neutral-400 dark:text-neutral-500">
                  <div className="text-center">
                    <AlertCircle className="mx-auto h-12 w-12 mb-2 opacity-50" />
                    <p>Media preview unavailable</p>
                    <p className="mt-1 text-sm">
                      Preview unavailable for older analyses.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
