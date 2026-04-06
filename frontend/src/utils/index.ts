/**
 * Utility Functions
 *
 * Common utility functions used throughout the application.
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// =============================================================================
// Class Name Utilities
// =============================================================================

/**
 * Merge Tailwind CSS classes with conflict resolution.
 *
 * @example
 * cn('px-4 py-2', isLarge && 'px-6 py-4', className)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// =============================================================================
// Formatting Utilities
// =============================================================================

/**
 * Format bytes to human-readable string.
 *
 * @example
 * formatBytes(1024) // '1 KB'
 * formatBytes(1234567) // '1.18 MB'
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const value = parseFloat((bytes / Math.pow(k, i)).toFixed(dm));

  return `${value} ${sizes[i]}`;
}

/**
 * Format duration in seconds to human-readable string.
 *
 * @example
 * formatDuration(65) // '1:05'
 * formatDuration(3661) // '1:01:01'
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format percentage with optional decimals.
 *
 * @example
 * formatPercent(0.956) // '95.6%'
 * formatPercent(0.956, 0) // '96%'
 */
export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format confidence score with level.
 *
 * @example
 * formatConfidence(0.95) // { value: '95%', level: 'high' }
 */
export function formatConfidence(confidence: number): {
  value: string;
  level: 'low' | 'medium' | 'high' | 'very_high';
} {
  const percent = confidence * 100;
  let level: 'low' | 'medium' | 'high' | 'very_high';

  if (percent >= 95) {
    level = 'very_high';
  } else if (percent >= 85) {
    level = 'high';
  } else if (percent >= 70) {
    level = 'medium';
  } else {
    level = 'low';
  }

  return {
    value: `${percent.toFixed(1)}%`,
    level,
  };
}

/**
 * Format relative time.
 *
 * @example
 * formatRelativeTime(new Date(Date.now() - 60000)) // '1 minute ago'
 */
export function formatRelativeTime(date: Date | string): string {
  const now = new Date();
  const then = new Date(date);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  const intervals: [number, string, string][] = [
    [31536000, 'year', 'years'],
    [2592000, 'month', 'months'],
    [86400, 'day', 'days'],
    [3600, 'hour', 'hours'],
    [60, 'minute', 'minutes'],
    [1, 'second', 'seconds'],
  ];

  for (const [interval, singular, plural] of intervals) {
    const count = Math.floor(seconds / interval);
    if (count >= 1) {
      return `${count} ${count === 1 ? singular : plural} ago`;
    }
  }

  return 'just now';
}

// =============================================================================
// Validation Utilities
// =============================================================================

/**
 * Check if value is a valid video file.
 */
export function isVideoFile(file: File): boolean {
  const videoTypes = ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'];
  return videoTypes.includes(file.type);
}

/**
 * Check if value is a valid image file.
 */
export function isImageFile(file: File): boolean {
  const imageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  return imageTypes.includes(file.type);
}

/**
 * Check if file is within size limit.
 */
export function isWithinSizeLimit(file: File, maxSizeBytes: number): boolean {
  return file.size <= maxSizeBytes;
}

/**
 * Validate file for upload.
 */
export function validateFile(
  file: File,
  options: {
    maxSize?: number;
    allowedTypes?: string[];
  } = {}
): { valid: boolean; error?: string } {
  const { maxSize = 500 * 1024 * 1024, allowedTypes } = options;

  // Check size
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File size exceeds ${formatBytes(maxSize)} limit`,
    };
  }

  // Check type if specified
  if (allowedTypes && !allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: `File type ${file.type} is not allowed`,
    };
  }

  return { valid: true };
}

// =============================================================================
// Async Utilities
// =============================================================================

/**
 * Sleep for specified milliseconds.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Debounce function execution.
 */
export function debounce<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Throttle function execution.
 */
export function throttle<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// =============================================================================
// ID Utilities
// =============================================================================

/**
 * Generate a unique ID.
 */
export function generateId(prefix = ''): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 9);
  return prefix ? `${prefix}_${timestamp}${random}` : `${timestamp}${random}`;
}

// =============================================================================
// Object Utilities
// =============================================================================

/**
 * Deep clone an object.
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Check if object is empty.
 */
export function isEmpty(obj: Record<string, unknown>): boolean {
  return Object.keys(obj).length === 0;
}

/**
 * Pick specified keys from object.
 */
export function pick<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  return keys.reduce(
    (result, key) => {
      if (key in obj) {
        result[key] = obj[key];
      }
      return result;
    },
    {} as Pick<T, K>
  );
}

/**
 * Omit specified keys from object.
 */
export function omit<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj };
  keys.forEach((key) => delete result[key]);
  return result;
}
