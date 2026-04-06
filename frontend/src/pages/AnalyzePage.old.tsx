/**
 * Analyze Page
 *
 * File upload and analysis initiation page.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import {
  Shield,
  Settings2,
  Cpu,
  Layers,
  Eye,
  Zap,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import { UploadZone } from '@/components/analysis/UploadZone';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { useCreateAnalysis } from '@/hooks';
import { useAnalysisStore } from '@/store';
import { cn } from '@/utils';

// =============================================================================
// Types
// =============================================================================

interface AnalysisOptions {
  useEnsemble: boolean;
  generateHeatmaps: boolean;
  extractFrames: boolean;
}

// =============================================================================
// Component
// =============================================================================

export default function AnalyzePage() {
  const navigate = useNavigate();
  const [showOptions, setShowOptions] = useState(false);
  const [options, setOptions] = useState<AnalysisOptions>({
    useEnsemble: true,
    generateHeatmaps: true,
    extractFrames: true,
  });

  const { mutateAsync: createAnalysis, isPending: isUploading } = useCreateAnalysis();
  const { currentProgress } = useAnalysisStore();

  // Handle file selection
  const handleFilesSelected = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;

      // For now, handle single file
      const file = files[0];
      if (!file) return;

      try {
        const analysis = await createAnalysis({
          file,
          options: {
            useEnsemble: options.useEnsemble,
            generateHeatmaps: options.generateHeatmaps,
            extractFrames: options.extractFrames,
          },
        });

        toast.success('Analysis started!');
        navigate(`/results/${analysis.id}`);
      } catch (error) {
        toast.error(
          error instanceof Error ? error.message : 'Failed to start analysis'
        );
      }
    },
    [createAnalysis, navigate, options]
  );

  // Toggle option
  const toggleOption = (key: keyof AnalysisOptions) => {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500">
          <Shield className="h-8 w-8 text-white" />
        </div>
        <h1 className="mt-6 text-3xl font-bold text-white">Analyze Media</h1>
        <p className="mt-2 text-neutral-400">
          Upload a video or image to check for deepfake manipulation
        </p>
      </motion.div>

      {/* Upload Zone */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <UploadZone
          onFilesSelected={handleFilesSelected}
          disabled={isUploading}
          maxFiles={1}
        />
      </motion.div>

      {/* Upload Progress */}
      <AnimatePresence>
        {isUploading && currentProgress && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card variant="glass">
              <div className="flex items-center gap-4 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-500/20">
                  <Zap className="h-5 w-5 animate-pulse text-primary-400" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-white">Uploading file...</p>
                  <Progress
                    value={currentProgress.percentage}
                    variant="gradient"
                    className="mt-2"
                  />
                </div>
                <span className="text-sm font-medium text-primary-400">
                  {currentProgress.percentage}%
                </span>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Analysis Options */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card variant="default">
          <button
            onClick={() => setShowOptions(!showOptions)}
            className="flex w-full items-center justify-between p-6"
          >
            <div className="flex items-center gap-3">
              <Settings2 className="h-5 w-5 text-neutral-400" />
              <span className="font-medium text-white">Analysis Options</span>
              <Badge variant="neutral" size="sm">
                Advanced
              </Badge>
            </div>
            {showOptions ? (
              <ChevronUp className="h-5 w-5 text-neutral-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-neutral-400" />
            )}
          </button>

          <AnimatePresence>
            {showOptions && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="space-y-4 border-t border-neutral-800 p-6">
                  {/* Ensemble Option */}
                  <OptionToggle
                    icon={Layers}
                    title="Multi-Model Ensemble"
                    description="Use all available models for higher accuracy (recommended)"
                    enabled={options.useEnsemble}
                    onToggle={() => toggleOption('useEnsemble')}
                  />

                  {/* Heatmaps Option */}
                  <OptionToggle
                    icon={Eye}
                    title="Generate Heatmaps"
                    description="Visual explanations showing detected manipulation areas"
                    enabled={options.generateHeatmaps}
                    onToggle={() => toggleOption('generateHeatmaps')}
                  />

                  {/* Frame Extraction Option */}
                  <OptionToggle
                    icon={Cpu}
                    title="Frame Analysis"
                    description="Analyze individual frames for detailed temporal analysis"
                    enabled={options.extractFrames}
                    onToggle={() => toggleOption('extractFrames')}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </motion.div>

      {/* Info Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card variant="glass" padding="sm">
          <div className="flex gap-4 p-4">
            <Info className="h-5 w-5 flex-shrink-0 text-primary-400" />
            <div className="text-sm text-neutral-400">
              <p>
                <strong className="text-white">Supported formats:</strong> MP4, WebM, MOV, JPG, PNG
              </p>
              <p className="mt-1">
                <strong className="text-white">Max file size:</strong> 500 MB
              </p>
              <p className="mt-1">
                Analysis typically completes in 2-10 seconds depending on video length.
              </p>
            </div>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}

// =============================================================================
// Option Toggle Component
// =============================================================================

function OptionToggle({
  icon: Icon,
  title,
  description,
  enabled,
  onToggle,
}: {
  icon: typeof Layers;
  title: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className="flex w-full items-start gap-4 rounded-xl p-4 text-left transition-colors hover:bg-neutral-800/30"
    >
      <div
        className={cn(
          'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl transition-colors',
          enabled ? 'bg-primary-500/20 text-primary-400' : 'bg-neutral-800 text-neutral-500'
        )}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1">
        <p className="font-medium text-white">{title}</p>
        <p className="mt-1 text-sm text-neutral-400">{description}</p>
      </div>
      <div
        className={cn(
          'relative h-6 w-11 flex-shrink-0 rounded-full transition-colors',
          enabled ? 'bg-primary-500' : 'bg-neutral-700'
        )}
      >
        <div
          className={cn(
            'absolute top-1 h-4 w-4 rounded-full bg-white transition-all',
            enabled ? 'left-6' : 'left-1'
          )}
        />
      </div>
    </button>
  );
}
