/**
 * Settings Page
 *
 * Application settings and preferences.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  User,
  Bell,
  Shield,
  Moon,
  Sun,
  Monitor,
  Key,
  Trash2,
  Download,
  RefreshCw,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useTheme } from '@/store';
import { cn } from '@/utils';

// =============================================================================
// Component
// =============================================================================

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [notifications, setNotifications] = useState(true);
  const [autoDelete, setAutoDelete] = useState(false);

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">Settings</h1>
        <p className="mt-1 text-neutral-500 dark:text-neutral-400">Manage your preferences and account</p>
      </div>

      {/* Appearance */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card variant="default">
          <CardHeader
            title="Appearance"
            description="Customize how Aletheia looks on your device"
          />
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <ThemeOption
                icon={Moon}
                label="Dark"
                selected={theme === 'dark'}
                onClick={() => setTheme('dark')}
              />
              <ThemeOption
                icon={Sun}
                label="Light"
                selected={theme === 'light'}
                onClick={() => setTheme('light')}
              />
              <ThemeOption
                icon={Monitor}
                label="System"
                selected={theme === 'system'}
                onClick={() => setTheme('system')}
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Notifications */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card variant="default">
          <CardHeader
            title="Notifications"
            description="Configure how you receive updates"
          />
          <CardContent>
            <div className="space-y-4">
              <SettingToggle
                icon={Bell}
                title="Analysis Complete"
                description="Get notified when your analysis finishes"
                enabled={notifications}
                onToggle={() => setNotifications(!notifications)}
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Privacy */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card variant="default">
          <CardHeader
            title="Privacy & Data"
            description="Control your data and privacy settings"
          />
          <CardContent>
            <div className="space-y-4">
              <SettingToggle
                icon={Trash2}
                title="Auto-delete analyses"
                description="Automatically delete analyses after 30 days"
                enabled={autoDelete}
                onToggle={() => setAutoDelete(!autoDelete)}
              />

              <div className="flex items-center justify-between rounded-xl bg-neutral-100 p-4 dark:bg-neutral-800/30">
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white dark:bg-neutral-800 shadow-sm border border-neutral-200 dark:border-neutral-700">
                    <Download className="h-5 w-5 text-neutral-500 dark:text-neutral-400" />
                  </div>
                  <div>
                    <p className="font-medium text-neutral-900 dark:text-white">Export Data</p>
                    <p className="text-sm text-neutral-500 dark:text-neutral-400">
                      Download all your analysis data
                    </p>
                  </div>
                </div>
                <Button variant="secondary" size="sm">
                  Export
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* API Keys */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card variant="default">
          <CardHeader
            title="API Access"
            description="Manage API keys for programmatic access"
            action={<Badge variant="accent">Coming Soon</Badge>}
          />
          <CardContent>
            <div className="rounded-xl border border-dashed border-neutral-300 bg-neutral-50 p-8 text-center dark:border-neutral-700 dark:bg-neutral-800/30">
              <Key className="mx-auto h-8 w-8 text-neutral-400 dark:text-neutral-600" />
              <p className="mt-4 text-neutral-500 dark:text-neutral-400">
                API access will be available in a future update
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Danger Zone */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card variant="default" className="border-danger-200 bg-danger-50 dark:border-danger-500/20 dark:bg-transparent">
          <CardHeader
            title="Danger Zone"
            description="Irreversible and destructive actions"
          />
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-danger-600 dark:text-white">Delete All Data</p>
                <p className="text-sm text-danger-500 dark:text-neutral-400">
                  Permanently delete all your analyses and account data
                </p>
              </div>
              <Button variant="danger" size="sm">
                Delete Everything
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Version Info */}
      <div className="text-center text-sm text-neutral-500 dark:text-neutral-500">
        <p>Aletheia v1.0.0</p>
        <p className="mt-1">Enterprise Deepfake Detection Platform</p>
      </div>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function ThemeOption({
  icon: Icon,
  label,
  selected,
  onClick,
}: {
  icon: typeof Moon;
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-3 rounded-xl px-4 py-3 transition-all',
        selected
          ? 'bg-primary-50 text-primary-600 ring-2 ring-primary-500 dark:bg-primary-500/20 dark:text-primary-400 dark:ring-primary-500/50'
          : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200 hover:text-neutral-900 border border-transparent dark:bg-neutral-800/50 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white dark:border-neutral-800'
      )}
    >
      <Icon className="h-5 w-5" />
      <span className="font-medium">{label}</span>
    </button>
  );
}

function SettingToggle({
  icon: Icon,
  title,
  description,
  enabled,
  onToggle,
}: {
  icon: typeof Bell;
  title: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className="flex w-full items-center justify-between rounded-xl bg-neutral-100 p-4 text-left transition-colors hover:bg-neutral-200 dark:bg-neutral-800/30 dark:hover:bg-neutral-800/50 border border-transparent dark:border-neutral-800"
    >
      <div className="flex items-center gap-4">
        <div
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-xl transition-colors shadow-sm',
            enabled ? 'bg-primary-500/10 text-primary-600 dark:bg-primary-500/20 dark:text-primary-400 border border-primary-500/20' : 'bg-white text-neutral-500 border border-neutral-200 dark:bg-neutral-800 dark:text-neutral-500 dark:border-neutral-700'
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="font-medium text-neutral-900 dark:text-white">{title}</p>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">{description}</p>
        </div>
      </div>
      <div
        className={cn(
          'relative h-6 w-11 rounded-full transition-colors',
          enabled ? 'bg-primary-500' : 'bg-neutral-300 dark:bg-neutral-700'
        )}
      >
        <div
          className={cn(
            'absolute top-1 h-4 w-4 rounded-full bg-white transition-all shadow-sm',
            enabled ? 'left-6' : 'left-1'
          )}
        />
      </div>
    </button>
  );
}
