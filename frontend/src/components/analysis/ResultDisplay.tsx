/**
 * Result Display Component
 *
 * Displays analysis results with confidence visualization.
 */

import { motion } from 'framer-motion';
import {
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  TrendingUp,
  TrendingDown,
  Clock,
  Cpu,
  Eye,
} from 'lucide-react';
import { cn, formatPercent } from '@/utils';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge, StatusBadge, ConfidenceBadge } from '@/components/ui/Badge';
import { CircularProgress } from '@/components/ui/Progress';
import type { Analysis, ModelResult } from '@/types/api';

// =============================================================================
// Types
// =============================================================================

interface ResultDisplayProps {
  analysis: Analysis;
  className?: string;
}

// =============================================================================
// Helper Components
// =============================================================================

function ResultIcon({ prediction }: { prediction: 'real' | 'fake' | 'uncertain' | null }) {
  const config = {
    real: {
      Icon: ShieldCheck,
      bgClass: 'bg-success-500/20',
      iconClass: 'text-success-400',
    },
    fake: {
      Icon: ShieldAlert,
      bgClass: 'bg-danger-500/20',
      iconClass: 'text-danger-400',
    },
    uncertain: {
      Icon: ShieldQuestion,
      bgClass: 'bg-warning-500/20',
      iconClass: 'text-warning-400',
    },
    null: {
      Icon: ShieldQuestion,
      bgClass: 'bg-neutral-700/50',
      iconClass: 'text-neutral-400',
    },
  };

  const { Icon, bgClass, iconClass } = config[prediction ?? 'null'];

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={cn('flex h-20 w-20 items-center justify-center rounded-2xl', bgClass)}
    >
      <Icon className={cn('h-10 w-10', iconClass)} />
    </motion.div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  trend,
}: {
  icon: typeof Clock;
  label: string;
  value: string;
  trend?: 'up' | 'down';
}) {
  return (
    <div className="rounded-xl bg-neutral-800/30 p-4">
      <div className="flex items-center gap-2 text-neutral-400">
        <Icon className="h-4 w-4" />
        <span className="text-sm">{label}</span>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span className="text-xl font-semibold text-white">{value}</span>
        {trend && (
          <span
            className={cn(
              'flex items-center text-xs',
              trend === 'up' ? 'text-success-400' : 'text-danger-400'
            )}
          >
            {trend === 'up' ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
          </span>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function ResultDisplay({ analysis, className }: ResultDisplayProps) {
  const prediction = analysis.prediction ?? null;
  const confidence = analysis.confidence ?? null;
  const modelResults = analysis.modelResults ?? [];
  const processingTime = analysis.processingTime ?? null;
  const frames = analysis.frames ?? [];
  const framesAnalyzed = (analysis as any).framesAnalyzed ?? frames.length;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Main Result Card */}
      <Card variant="glass" padding="lg">
        <div className="flex flex-col items-center text-center sm:flex-row sm:text-left">
          {/* Result icon */}
          <ResultIcon prediction={prediction} />

          {/* Result text */}
          <div className="mt-4 sm:ml-6 sm:mt-0">
            <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
              <StatusBadge status={prediction ?? 'pending'} />
              {confidence !== null && <ConfidenceBadge confidence={confidence} />}
            </div>

            <h2 className="mt-3 text-2xl font-bold text-white">
              {prediction === 'fake'
                ? 'Manipulation Detected'
                : prediction === 'real'
                  ? 'Authentic Content'
                  : 'Analysis Uncertain'}
            </h2>

            <p className="mt-2 text-neutral-400">
              {prediction === 'fake'
                ? 'Our AI models have detected signs of manipulation in this media.'
                : prediction === 'real'
                  ? 'No signs of manipulation were detected in this media.'
                  : 'Unable to make a confident determination. Additional analysis may be needed.'}
            </p>
          </div>

          {/* Confidence gauge */}
          {confidence !== null && (
            <div className="mt-6 sm:ml-auto sm:mt-0">
              <CircularProgress
                value={confidence > 1 ? confidence : confidence * 100}
                size={100}
                strokeWidth={8}
                variant={prediction === 'fake' ? 'danger' : prediction === 'real' ? 'success' : 'warning'}
              />
            </div>
          )}
        </div>
      </Card>

      {/* Stats Row */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          icon={Clock}
          label="Processing Time"
          value={processingTime ? `${processingTime.toFixed(1)}s` : '--'}
        />
        <StatCard
          icon={Eye}
          label="Frames Analyzed"
          value={framesAnalyzed.toString()}
        />
        <StatCard
          icon={Cpu}
          label="Models Used"
          value={modelResults.length > 0 ? modelResults.length.toString() : '1'}
        />
      </div>

      {/* Model Results */}
      {modelResults.length > 0 && (
        <Card variant="default">
          <CardHeader
            title="Model Analysis"
            description="Individual model predictions and confidence scores"
          />
          <CardContent>
            <div className="space-y-4">
              {modelResults.map((result, index) => (
                <ModelResultRow key={index} result={result} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// =============================================================================
// Model Result Row
// =============================================================================

function ModelResultRow({ result }: { result: ModelResult }) {
  const { modelName, prediction, confidence, fakeScore, processingTime } = result;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center justify-between rounded-xl bg-neutral-800/30 p-4"
    >
      {/* Model info */}
      <div className="flex items-center gap-4">
        <div
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-xl',
            prediction === 'fake'
              ? 'bg-danger-500/20 text-danger-400'
              : 'bg-success-500/20 text-success-400'
          )}
        >
          {prediction === 'fake' ? (
            <ShieldAlert className="h-5 w-5" />
          ) : (
            <ShieldCheck className="h-5 w-5" />
          )}
        </div>

        <div>
          <p className="font-medium text-white">{modelName}</p>
          <p className="text-sm text-neutral-400">
            Processed in {(processingTime * 1000).toFixed(0)}ms
          </p>
        </div>
      </div>

      {/* Scores */}
      <div className="flex items-center gap-6">
        {/* Score bars */}
        <div className="hidden w-48 sm:block">
          <div className="flex h-2 overflow-hidden rounded-full bg-neutral-700">
            <div
              className="bg-success-500 transition-all duration-500"
              style={{ width: `${(1 - fakeScore) * 100}%` }}
            />
            <div
              className="bg-danger-500 transition-all duration-500"
              style={{ width: `${fakeScore * 100}%` }}
            />
          </div>
          <div className="mt-1 flex justify-between text-xs text-neutral-500">
            <span>Real {formatPercent(1 - fakeScore, 0)}</span>
            <span>Fake {formatPercent(fakeScore, 0)}</span>
          </div>
        </div>

        {/* Confidence badge */}
        <div className="text-right">
          <Badge
            variant={prediction === 'fake' ? 'danger' : 'success'}
            size="lg"
          >
            {formatPercent(confidence)}
          </Badge>
        </div>
      </div>
    </motion.div>
  );
}
