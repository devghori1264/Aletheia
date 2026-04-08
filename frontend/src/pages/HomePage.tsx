/**
 * Home Page - Aletheia Deepfake Detection Platform
 * 
 * Main dashboard with clean, professional interface.
 * Displays real statistics calculated from analysis data.
 */

import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Upload,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Clock,
  ArrowRight,
  Activity,
  FileVideo,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { useAnalysisList, useAnalysisStats } from '@/hooks';
import { useTheme } from '@/store';
import { formatRelativeTime, cn } from '@/utils';

export default function HomePage() {
  const { data: recentAnalyses, isLoading: isListLoading } = useAnalysisList({ page: 1, pageSize: 5 });
  const { data: statsData, isLoading: isStatsLoading } = useAnalysisStats();

  const stats = useMemo(() => {
    if (!statsData) {
      return [
        { label: 'Total Scans', value: '-', icon: FileVideo, iconColor: 'text-blue-400' },
        { label: 'Authentic', value: '-', icon: CheckCircle2, iconColor: 'text-green-400' },
        { label: 'Suspicious', value: '-', icon: AlertTriangle, iconColor: 'text-amber-400' },
        { label: 'Avg. Time', value: '-', icon: Clock, iconColor: 'text-purple-400' },
      ];
    }

    return [
      { label: 'Total Scans', value: statsData.totalAnalyses.toString(), icon: FileVideo, iconColor: 'text-blue-400' },
      { label: 'Authentic', value: statsData.realDetected.toString(), icon: CheckCircle2, iconColor: 'text-green-400' },
      { label: 'Suspicious', value: statsData.fakeDetected.toString(), icon: AlertTriangle, iconColor: 'text-amber-400' },
      { label: 'Avg. Time', value: `${statsData.averageProcessingTime.toFixed(1)}s`, icon: Clock, iconColor: 'text-purple-400' },
    ];
  }, [statsData]);

  const recentItems = recentAnalyses?.items || [];
  const isLoading = isListLoading || isStatsLoading;

  return (
    <div className="min-h-screen">
      {/* Header Section */}
      <div className="mb-6 border-b border-neutral-200 pb-6 sm:mb-8 sm:pb-8 dark:border-neutral-800/50">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-neutral-900 sm:text-3xl dark:text-white">
              Media Verification Dashboard
            </h1>
            <p className="mt-2 text-sm text-neutral-600 sm:text-base dark:text-neutral-400">
              Analyze video content for authenticity using deep learning
            </p>
          </div>
          <Link to="/analyze" className="w-full sm:w-auto">
            <Button size="lg" className="w-full gap-2 sm:w-auto">
              <Upload className="h-5 w-5" />
              New Analysis
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:mb-8 sm:gap-4 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} variant="default" padding="md">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-neutral-500 sm:text-sm dark:text-neutral-400">
                  {stat.label}
                </p>
                <p className="mt-1 text-2xl font-semibold text-neutral-900 sm:mt-2 sm:text-3xl dark:text-white">
                   {stat.value}
                </p>
              </div>
              <div className="flex-shrink-0 rounded-lg p-2 bg-neutral-100 sm:p-3 dark:bg-neutral-800">
                <stat.icon className={`h-5 w-5 sm:h-6 sm:w-6 ${stat.iconColor}`} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Activity */}
        <div className="lg:col-span-2">
          <Card variant="default">
            <CardHeader
              title="Recent Activity"
              description="Latest verification requests"
              action={
                <Link to="/history">
                  <Button variant="ghost" size="sm" className="gap-1">
                    View all
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              }
            />
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="h-20 animate-pulse rounded-lg bg-neutral-100 dark:bg-neutral-800/40" />
                  ))}
                </div>
              ) : recentItems.length > 0 ? (
                <div className="space-y-2">
                  {recentItems.map((analysis) => (
                    <Link
                      key={analysis.id}
                      to={`/results/${analysis.id}`}
                      className={cn(
                        'block rounded-lg border p-3 transition-all sm:p-4',
                        'border-neutral-200 bg-white hover:border-neutral-300 hover:bg-neutral-50',
                        'dark:border-neutral-800 dark:bg-neutral-900/50 dark:hover:border-neutral-700 dark:hover:bg-neutral-900'
                      )}
                    >
                      <div className="flex items-center gap-3 sm:gap-4">
                        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-md bg-neutral-100 sm:h-12 sm:w-12 dark:bg-neutral-800">
                          <FileVideo className="h-4 w-4 text-neutral-500 sm:h-5 sm:w-5 dark:text-neutral-400" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-neutral-900 sm:text-base dark:text-white">
                            {analysis.fileName}
                          </p>
                          <p className="text-xs text-neutral-400 sm:text-sm dark:text-neutral-500">
                            {formatRelativeTime(analysis.createdAt)}
                          </p>
                        </div>
                        <StatusBadge status={analysis.prediction ?? 'pending'} />
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center sm:py-16">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-neutral-100 sm:h-16 sm:w-16 dark:bg-neutral-800">
                    <Activity className="h-7 w-7 text-neutral-400 sm:h-8 sm:w-8 dark:text-neutral-600" />
                  </div>
                  <h3 className="mb-2 text-base font-medium text-neutral-900 sm:text-lg dark:text-white">
                    No activity yet
                  </h3>
                  <p className="mb-6 text-sm text-neutral-500 sm:text-base dark:text-neutral-400">
                    Start analyzing media to see results here
                  </p>
                  <Link to="/analyze">
                     <Button>Upload First Video</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* System Info Sidebar */}
        <div className="space-y-6">
          {/* System Status */}
          <Card variant="default">
            <CardHeader title="System Status" />
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-sm text-neutral-700 dark:text-neutral-300">Detection Engine</span>
                  </div>
                  <span className="text-xs text-neutral-400 dark:text-neutral-500">Online</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-sm text-neutral-700 dark:text-neutral-300">API Server</span>
                  </div>
                  <span className="text-xs text-neutral-400 dark:text-neutral-500">Healthy</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-sm text-neutral-700 dark:text-neutral-300">Database</span>
                  </div>
                  <span className="text-xs text-neutral-400 dark:text-neutral-500">Connected</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card variant="default">
            <CardHeader title="Quick Actions" />
            <CardContent>
              <div className="space-y-2">
                <Link to="/analyze" className="block">
                  <button className={cn(
                    'w-full rounded-lg border p-3 text-left transition-all',
                    'border-neutral-200 bg-white hover:border-neutral-300 hover:bg-neutral-50',
                    'dark:border-neutral-800 dark:bg-neutral-900/50 dark:hover:border-neutral-700 dark:hover:bg-neutral-900'
                  )}>
                    <div className="flex items-center gap-3">
                      <Upload className="h-5 w-5 text-blue-400" />
                      <span className="text-sm font-medium text-neutral-900 dark:text-white">Upload Video</span>
                    </div>
                  </button>
                </Link>
                <Link to="/history" className="block">
                  <button className={cn(
                    'w-full rounded-lg border p-3 text-left transition-all',
                    'border-neutral-200 bg-white hover:border-neutral-300 hover:bg-neutral-50',
                    'dark:border-neutral-800 dark:bg-neutral-900/50 dark:hover:border-neutral-700 dark:hover:bg-neutral-900'
                  )}>
                    <div className="flex items-center gap-3">
                      <Clock className="h-5 w-5 text-purple-400" />
                      <span className="text-sm font-medium text-neutral-900 dark:text-white">View History</span>
                    </div>
                  </button>
                </Link>
                <Link to="/settings" className="block">
                  <button className={cn(
                    'w-full rounded-lg border p-3 text-left transition-all',
                    'border-neutral-200 bg-white hover:border-neutral-300 hover:bg-neutral-50',
                    'dark:border-neutral-800 dark:bg-neutral-900/50 dark:hover:border-neutral-700 dark:hover:bg-neutral-900'
                  )}>
                    <div className="flex items-center gap-3">
                      <Shield className="h-5 w-5 text-green-400" />
                      <span className="text-sm font-medium text-neutral-900 dark:text-white">Settings</span>
                    </div>
                  </button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* About */}
          <Card variant="default">
            <CardHeader title="About Aletheia" />
            <CardContent>
              <p className="text-sm leading-relaxed text-neutral-600 dark:text-neutral-400">
                Advanced deepfake detection powered by ensemble deep learning models,
                providing reliable verification of video authenticity.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
