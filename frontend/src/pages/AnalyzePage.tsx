/**
 * Analyze Page - Video Upload and Analysis
 * 
 * Clean, professional interface for media upload
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
import { useCreateAnalysis } from '@/hooks';
import { useAnalysisStore } from '@/store';

interface AnalysisOptions {
  useEnsemble: boolean;
  generateHeatmaps: boolean;
  extractFrames: boolean;
}

export default function AnalyzePage() {
  const navigate = useNavigate();
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
  const isServerProcessing = analysisPhase === 'uploading' && 
    currentProgress && currentProgress.percentage >= 100;

  const toggleOption = (key: keyof AnalysisOptions) => {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="mx-auto max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Analyze Video
        </h1>
        <p className="mt-2 text-neutral-400">
          Upload a video file to check for signs of manipulation
        </p>
      </div>

      {/* Main Upload Area */}
      <Card variant="default" className="mb-6">
        <CardContent className="p-8">
          <UploadZone
            onFilesSelected={handleFilesSelected}
            accept={{ 'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm'] }}
            maxFiles={1}
            maxSize={500 * 1024 * 1024} // 500MB
            disabled={isUploading}
          />

          {(isUploading || isServerProcessing) && (
            <div className="mt-6 rounded-lg border border-neutral-800 bg-neutral-900/50 p-4">
              {isServerProcessing ? (
                <>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="text-neutral-300 flex items-center gap-2">
                      <span className="inline-block h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                      Analyzing video... This may take a moment
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-neutral-800">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 animate-pulse"
                      style={{ width: '100%' }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-neutral-500">
                    Running deepfake detection on extracted frames...
                  </p>
                </>
              ) : currentProgress ? (
                <>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="text-neutral-300">Uploading...</span>
                    <span className="font-medium text-white">
                      {currentProgress.percentage}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-neutral-800">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${currentProgress.percentage}%` }}
                    />
                  </div>
                </>
              ) : (
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-neutral-300 flex items-center gap-2">
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
            <Settings className="h-5 w-5 text-neutral-400" />
          }
        />
        <CardContent>
          <div className="space-y-4">
            {/* Ensemble Models */}
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-white">
                    Use Ensemble Models
                  </h3>
                  {options.useEnsemble && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                </div>
                <p className="mt-1 text-sm text-neutral-400">
                  Combine multiple models for higher accuracy (recommended)
                </p>
              </div>
              <button
                onClick={() => toggleOption('useEnsemble')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  options.useEnsemble ? 'bg-blue-600' : 'bg-neutral-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    options.useEnsemble ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Heatmaps */}
            <div className="flex items-start justify-between border-t border-neutral-800 pt-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-white">
                    Generate Heatmaps
                  </h3>
                  {options.generateHeatmaps && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                </div>
                <p className="mt-1 text-sm text-neutral-400">
                  Visual highlighting of suspicious areas
                </p>
              </div>
              <button
                onClick={() => toggleOption('generateHeatmaps')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  options.generateHeatmaps ? 'bg-blue-600' : 'bg-neutral-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    options.generateHeatmaps ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Frame Extraction */}
            <div className="flex items-start justify-between border-t border-neutral-800 pt-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-white">
                    Extract Key Frames
                  </h3>
                  {options.extractFrames && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                </div>
                <p className="mt-1 text-sm text-neutral-400">
                  Save individual frames for detailed inspection
                </p>
              </div>
              <button
                onClick={() => toggleOption('extractFrames')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  options.extractFrames ? 'bg-blue-600' : 'bg-neutral-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    options.extractFrames ? 'translate-x-6' : 'translate-x-1'
                  }`}
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
          <div className="space-y-3 text-sm text-neutral-400">
            <div className="flex items-start gap-3">
              <FileVideo className="mt-0.5 h-4 w-4 flex-shrink-0 text-neutral-500" />
              <div>
                <p className="text-neutral-300">Video Files</p>
                <p>MP4, MOV, AVI, MKV, WebM</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Upload className="mt-0.5 h-4 w-4 flex-shrink-0 text-neutral-500" />
              <div>
                <p className="text-neutral-300">Max File Size</p>
                <p>500 MB per video</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-neutral-500" />
              <div>
                <p className="text-neutral-300">Processing Time</p>
                <p>Typically 30-60 seconds depending on video length</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
