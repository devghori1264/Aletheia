/**
 * Home Page - Aletheia Deepfake Detection Platform
 * 
 * Main dashboard with clean, professional interface
 */

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
import { useAnalysisList } from '@/hooks';
import { formatRelativeTime } from '@/utils';

const stats = [
  { label: 'Total Scans', value: '0', icon: FileVideo, iconColor: 'text-blue-400' },
  { label: 'Authentic', value: '0', icon: CheckCircle2, iconColor: 'text-green-400' },
  { label: 'Suspicious', value: '0', icon: AlertTriangle, iconColor: 'text-amber-400' },
  { label: 'Avg. Time', value: '-', icon: Clock, iconColor: 'text-purple-400' },
];

export default function HomePage() {
  const { data, isLoading } = useAnalysisList({ page: 1, pageSize: 5 });

  return (
    <div className="min-h-screen">
      {/* Header Section */}
      <div className="mb-8 border-b border-neutral-800 pb-8">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              Media Verification Dashboard
            </h1>
            <p className="mt-2 text-neutral-400">
              Analyze video content for authenticity using deep learning
            </p>
          </div>
          <Link to="/analyze">
            <Button size="lg" className="gap-2">
              <Upload className="h-5 w-5" />
              New Analysis
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} variant="default" padding="md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-400">{stat.label}</p>
                <p className="mt-2 text-3xl font-semibold text-white">{stat.value}</p>
              </div>
              <div className="rounded-lg bg-neutral-800 p-3">
                <stat.icon className={`h-6 w-6 ${stat.iconColor}`} />
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
                    <div key={i} className="h-20 animate-pulse rounded-lg bg-neutral-800/40" />
                  ))}
                </div>
              ) : data?.items.length ? (
                <div className="space-y-2">
                  {data.items.map((analysis) => (
                    <Link
                      key={analysis.id}
                      to={`/results/${analysis.id}`}
                      className="block rounded-lg border border-neutral-800 bg-neutral-900/50 p-4 transition-all hover:border-neutral-700 hover:bg-neutral-900"
                    >
                      <div className="flex items-center gap-4">
                        <div className="flex h-12 w-12 items-center justify-center rounded-md bg-neutral-800">
                          <FileVideo className="h-5 w-5 text-neutral-400" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium text-white">
                            {analysis.fileName}
                          </p>
                          <p className="text-sm text-neutral-500">
                            {formatRelativeTime(analysis.createdAt)}
                          </p>
                        </div>
                        <StatusBadge status={analysis.prediction ?? 'pending'} />
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-16 text-center">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-neutral-800">
                    <Activity className="h-8 w-8 text-neutral-600" />
                  </div>
                  <h3 className="mb-2 text-lg font-medium text-white">No activity yet</h3>
                  <p className="mb-6 text-neutral-400">
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
                    <span className="text-sm text-neutral-300">Detection Engine</span>
                  </div>
                  <span className="text-xs text-neutral-500">Online</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-sm text-neutral-300">API Server</span>
                  </div>
                  <span className="text-xs text-neutral-500">Healthy</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-sm text-neutral-300">Database</span>
                  </div>
                  <span className="text-xs text-neutral-500">Connected</span>
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
                  <button className="w-full rounded-lg border border-neutral-800 bg-neutral-900/50 p-3 text-left transition-all hover:border-neutral-700 hover:bg-neutral-900">
                    <div className="flex items-center gap-3">
                      <Upload className="h-5 w-5 text-blue-400" />
                      <span className="text-sm font-medium text-white">Upload Video</span>
                    </div>
                  </button>
                </Link>
                <Link to="/history" className="block">
                  <button className="w-full rounded-lg border border-neutral-800 bg-neutral-900/50 p-3 text-left transition-all hover:border-neutral-700 hover:bg-neutral-900">
                    <div className="flex items-center gap-3">
                      <Clock className="h-5 w-5 text-purple-400" />
                      <span className="text-sm font-medium text-white">View History</span>
                    </div>
                  </button>
                </Link>
                <Link to="/settings" className="block">
                  <button className="w-full rounded-lg border border-neutral-800 bg-neutral-900/50 p-3 text-left transition-all hover:border-neutral-700 hover:bg-neutral-900">
                    <div className="flex items-center gap-3">
                      <Shield className="h-5 w-5 text-green-400" />
                      <span className="text-sm font-medium text-white">Settings</span>
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
              <p className="text-sm leading-relaxed text-neutral-400">
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
