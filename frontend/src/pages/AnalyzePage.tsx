/**
 * Analyze Page - Video Upload and Analysis
 * 
 * Clean, professional interface for media upload.
 * Supports dark/light theme modes with responsive design.
 * Prominently displays privacy assurance to build user trust.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  Upload,
  FileVideo,
  AlertCircle,
  CheckCircle,
  Settings,
} from 'lucide-react';
import { UploadZone } from '@/components/analysis/UploadZone';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PrivacyBanner, PrivacyBadge } from '@/components/ui/PrivacyBanner';
import { useCreateAnalysis } from '@/hooks';
import { useAnalysisStore, useTheme } from '@/store';
import { cn } from '@/utils';

interface AnalysisOptions {
  useEnsemble: boolean;
  generateHeatmaps: boolean;
  extractFrames: boolean;
}

export default function AnalyzePage() {
  const navigate = useNavigate();
  const { resolvedTheme } = useTheme();
  const [options, setOptions] = useState<AnalysisOptions>({
    useEnsemble: true,
    generateHeatmaps: true,
    extractFrames: true,
  });

  const { mutateAsync: createAnalysis, isPending: isUploading } = useCreateAnalysis();
  const { currentProgress } = useAnalysisStore();

  const [analysisPhase, setAnalysisPhase] = useState<'idle' | 'uploading' | 'analyzing'>('idle');

  const handleFilesSelected = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;

      const file = files[0];
      if (!file) return;

      try {
        setAnalysisPhase('uploading');
        
        const analysis = await createAnalysis({
          file,
          options,
        });

        // If we get here, the server has finished processing
        setAnalysisPhase('idle');
        toast.success('Analysis complete!');
        navigate(`/results/${analysis.id}`);
      } catch (error) {
        setAnalysisPhase('idle');
        toast.error(
          error instanceof Error ? error.message : 'Analysis failed. Please try again.'
        );
      }
    },
    [createAnalysis, navigate, options]
  );

  // Detect when upload is done but server is still processing
  const isActuallyUploading = analysisPhase === 'uploading' && 
    currentProgress && currentProgress.percentage < 100;
  const isServerProcessing = analysisPhase === 'uploading' && 
    currentProgress && currentProgress.percentage >= 100;

  const toggleOption = (key: keyof AnalysisOptions) => {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const isDark = resolvedTheme === 'dark';

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-0">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className={cn(
          'text-2xl font-bold tracking-tight sm:text-3xl',
          isDark ? 'text-white' : 'text-neutral-900'
        )}>
          Analyze Video
        </h1>
        <p className={cn(
          'mt-2 text-sm sm:text-base',
          isDark ? 'text-neutral-400' : 'text-neutral-600'
        )}>
          Upload a video file to check for signs of manipulation
        </p>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          PRIVACY ASSURANCE BANNER
          Placed prominently before the upload zone to establish trust
          before users consider uploading sensitive content.
          ═══════════════════════════════════════════════════════════════════ */}
      <PrivacyBanner variant="inline" animate className="mb-6" />

      {/* Main Upload Area */}
      <Card variant="default" className="mb-6">
        <CardContent className="p-4 sm:p-8">
          <UploadZone
            onFilesSelected={handleFilesSelected}
            accept={{ 'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm'] }}
            maxFiles={1}
            maxSize={500 * 1024 * 1024} // 500MB
            disabled={isUploading}
          />
          
          {/* Privacy badge below upload zone for reinforcement */}
          <div className="mt-4 flex justify-center">
            <PrivacyBadge size="md" />
          </div>

          {(isUploading || isServerProcessing || isActuallyUploading) && (
            <div className={cn(
              'mt-6 rounded-lg border p-4',
              isDark 
                ? 'border-neutral-800 bg-neutral-900/50' 
                : 'border-neutral-200 bg-neutral-50'
            )}>
              {isActuallyUploading && currentProgress ? (
                <>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className={cn(
                      'flex items-center gap-2',
                      isDark ? 'text-neutral-300' : 'text-neutral-600'
                    )}>
                      <span className="inline-block h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                      Uploading video to server...
                    </span>
                    <span className={cn(
                      'font-medium',
                      isDark ? 'text-white' : 'text-neutral-900'
                    )}>
                      {currentProgress.percentage}%
                    </span>
                  </div>
                  <div className={cn(
                    'h-2 overflow-hidden rounded-full',
                    isDark ? 'bg-neutral-800' : 'bg-neutral-200'
                  )}>
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${currentProgress.percentage}%` }}
                    />
                  </div>
                  <p className={cn(
                    'mt-2 text-xs',
                    isDark ? 'text-neutral-500' : 'text-neutral-400'
                  )}>
                    Transferring file data...
                  </p>
                </>
              ) : isServerProcessing ? (
                <>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className={cn(
                      'flex items-center gap-2',
                      isDark ? 'text-neutral-300' : 'text-neutral-600'
                    )}>
                      <span className="inline-block h-2 w-2 rounded-full bg-purple-500 animate-pulse" />
                      Analyzing video... This may take a moment
                    </span>
                  </div>
                  <div className={cn(
                    'h-2 overflow-hidden rounded-full',
                    isDark ? 'bg-neutral-800' : 'bg-neutral-200'
                  )}>
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 animate-pulse"
                      style={{ width: '100%' }}
                    />
                  </div>
                  <p className={cn(
                    'mt-2 text-xs',
                    isDark ? 'text-neutral-500' : 'text-neutral-400'
                  )}>
                    Running deepfake detection on extracted frames...
                  </p>
                </>
              ) : (
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className={cn(
                    'flex items-center gap-2',
                    isDark ? 'text-neutral-300' : 'text-neutral-600'
                  )}>
                    <span className="inline-block h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                    Preparing upload...
                  </span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analysis Options */}
      <Card variant="default" className="mb-6">
        <CardHeader
          title="Analysis Settings"
          description="Configure detection parameters"
          action={
            <Settings className={isDark ? 'h-5 w-5 text-neutral-400' : 'h-5 w-5 text-neutral-500'} />
          }
        />
        <CardContent>
          <div className="space-y-4">
            {/* Ensemble Models */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className={cn(
                    'font-medium',
                    isDark ? 'text-white' : 'text-neutral-900'
                  )}>
                    Use Ensemble Models
                  </h3>
                  {options.useEnsemble && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                </div>
                <p className={cn(
                  'mt-1 text-sm',
                  isDark ? 'text-neutral-400' : 'text-neutral-500'
                )}>
                  Combine multiple models for higher accuracy (recommended)
                </p>
              </div>
              <button
                onClick={() => toggleOption('useEnsemble')}
                className={cn(
                  'relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors',
                  options.useEnsemble 
                    ? 'bg-blue-600' 
                    : isDark ? 'bg-neutral-700' : 'bg-neutral-300'
                )}
              >
                <span
                  className={cn(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    options.useEnsemble ? 'translate-x-6' : 'translate-x-1'
                  )}
                />
              </button>
            </div>

            {/* Heatmaps */}
            <div className={cn(
              'flex items-start justify-between gap-4 border-t pt-4',
              isDark ? 'border-neutral-800' : 'border-neutral-200'
            )}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className={cn(
                    'font-medium',
                    isDark ? 'text-white' : 'text-neutral-900'
                  )}>
                    Generate Heatmaps
                  </h3>
                  {options.generateHeatmaps && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                </div>
                <p className={cn(
                  'mt-1 text-sm',
                  isDark ? 'text-neutral-400' : 'text-neutral-500'
                )}>
                  Visual highlighting of suspicious areas
                </p>
              </div>
              <button
                onClick={() => toggleOption('generateHeatmaps')}
                className={cn(
                  'relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors',
                  options.generateHeatmaps 
                    ? 'bg-blue-600' 
                    : isDark ? 'bg-neutral-700' : 'bg-neutral-300'
                )}
              >
                <span
                  className={cn(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    options.generateHeatmaps ? 'translate-x-6' : 'translate-x-1'
                  )}
                />
              </button>
            </div>

            {/* Frame Extraction */}
            <div className={cn(
              'flex items-start justify-between gap-4 border-t pt-4',
              isDark ? 'border-neutral-800' : 'border-neutral-200'
            )}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className={cn(
                    'font-medium',
                    isDark ? 'text-white' : 'text-neutral-900'
                  )}>
                    Extract Key Frames
                  </h3>
                  {options.extractFrames && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                </div>
                <p className={cn(
                  'mt-1 text-sm',
                  isDark ? 'text-neutral-400' : 'text-neutral-500'
                )}>
                  Save individual frames for detailed inspection
                </p>
              </div>
              <button
                onClick={() => toggleOption('extractFrames')}
                className={cn(
                  'relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors',
                  options.extractFrames 
                    ? 'bg-blue-600' 
                    : isDark ? 'bg-neutral-700' : 'bg-neutral-300'
                )}
              >
                <span
                  className={cn(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    options.extractFrames ? 'translate-x-6' : 'translate-x-1'
                  )}
                />
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card variant="default">
        <CardHeader
          title="Supported Formats"
          action={<AlertCircle className="h-5 w-5 text-blue-400" />}
        />
        <CardContent>
          <div className={cn(
            'space-y-3 text-sm',
            isDark ? 'text-neutral-400' : 'text-neutral-500'
          )}>
            <div className="flex items-start gap-3">
              <FileVideo className={cn(
                'mt-0.5 h-4 w-4 flex-shrink-0',
                isDark ? 'text-neutral-500' : 'text-neutral-400'
              )} />
              <div>
                <p className={isDark ? 'text-neutral-300' : 'text-neutral-700'}>Video Files</p>
                <p>MP4, MOV, AVI, MKV, WebM</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Upload className={cn(
                'mt-0.5 h-4 w-4 flex-shrink-0',
                isDark ? 'text-neutral-500' : 'text-neutral-400'
              )} />
              <div>
                <p className={isDark ? 'text-neutral-300' : 'text-neutral-700'}>Max File Size</p>
                <p>500 MB per video</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <AlertCircle className={cn(
                'mt-0.5 h-4 w-4 flex-shrink-0',
                isDark ? 'text-neutral-500' : 'text-neutral-400'
              )} />
              <div>
                <p className={isDark ? 'text-neutral-300' : 'text-neutral-700'}>Processing Time</p>
                <p>Typically 30-60 seconds depending on video length</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
