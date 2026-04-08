/**
 * Custom Hooks
 *
 * Reusable React hooks for common patterns.
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analysisService, analysisKeys } from '@/services';
import type { Analysis, AnalysisOptions, PaginationParams } from '@/types/api';
import { useAnalysisStore } from '@/store';

// =============================================================================
// Analysis Hooks
// =============================================================================

/**
 * Hook for fetching analysis by ID.
 */
export function useAnalysis(id: string | undefined) {
  return useQuery({
    queryKey: analysisKeys.detail(id || ''),
    queryFn: () => analysisService.getById(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll while processing
      const data = query.state.data;
      if (data?.status === 'processing' || data?.status === 'pending') {
        return 2000; // Poll every 2 seconds
      }
      return false;
    },
  });
}

/**
 * Hook for fetching analysis list.
 */
export function useAnalysisList(params?: PaginationParams) {
  return useQuery({
    queryKey: analysisKeys.list(params || {}),
    queryFn: async () => {
      try {
        return await analysisService.getList(params);
      } catch (error) {
        // Return empty list if API fails
        return {
          items: [],
          meta: {
            page: 1,
            pageSize: 20,
            totalPages: 0,
            totalItems: 0,
          },
        };
      }
    },
  });
}

/**
 * Hook for fetching analysis stats.
 */
export function useAnalysisStats() {
  return useQuery({
    queryKey: analysisKeys.stats(),
    queryFn: async () => {
      try {
        return await analysisService.getStats();
      } catch (error) {
        return {
          totalAnalyses: 0,
          fakeDetected: 0,
          realDetected: 0,
          averageConfidence: 0,
          averageProcessingTime: 0,
        };
      }
    },
  });
}

/**
 * Hook for creating new analysis.
 */
export function useCreateAnalysis() {
  const queryClient = useQueryClient();
  const { setCurrentAnalysis, setIsUploading, setUploadProgress } = useAnalysisStore();

  return useMutation({
    mutationFn: ({
      file,
      options,
    }: {
      file: File;
      options?: AnalysisOptions;
    }) => {
      setIsUploading(true);
      return analysisService.create(file, options, (progress) => {
        setUploadProgress({ loaded: progress, total: 100, percentage: progress });
      });
    },
    onSuccess: (analysis) => {
      setCurrentAnalysis(analysis);
      queryClient.invalidateQueries({ queryKey: analysisKeys.lists() });
    },
    onSettled: () => {
      setIsUploading(false);
      setUploadProgress(null);
    },
  });
}

/**
 * Hook for cancelling analysis.
 */
export function useCancelAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => analysisService.cancel(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: analysisKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: analysisKeys.lists() });
    },
  });
}

/**
 * Hook for deleting analysis.
 */
export function useDeleteAnalysis() {
  const queryClient = useQueryClient();
  const { removeFromRecentAnalyses } = useAnalysisStore();

  return useMutation({
    mutationFn: (id: string) => analysisService.delete(id),
    onSuccess: (_, id) => {
      removeFromRecentAnalyses(id);
      queryClient.invalidateQueries({ queryKey: analysisKeys.lists() });
    },
  });
}

// =============================================================================
// UI Hooks
// =============================================================================

/**
 * Hook for detecting clicks outside an element.
 */
export function useClickOutside<T extends HTMLElement>(
  callback: () => void
): React.RefObject<T | null> {
  const ref = useRef<T>(null);

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    };

    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [callback]);

  return ref;
}

/**
 * Hook for keyboard shortcuts.
 */
export function useKeyboardShortcut(
  key: string,
  callback: () => void,
  options: { ctrl?: boolean; shift?: boolean; alt?: boolean; meta?: boolean } = {}
): void {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const { ctrl = false, shift = false, alt = false, meta = false } = options;

      if (
        event.key.toLowerCase() === key.toLowerCase() &&
        event.ctrlKey === ctrl &&
        event.shiftKey === shift &&
        event.altKey === alt &&
        event.metaKey === meta
      ) {
        event.preventDefault();
        callback();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [key, callback, options]);
}

/**
 * Hook for debounced value.
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for local storage state.
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (error) {
        console.error('Error saving to localStorage:', error);
      }
    },
    [key, storedValue]
  );

  return [storedValue, setValue];
}

/**
 * Hook for media query.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);

    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [query]);

  return matches;
}

/**
 * Hook for responsive breakpoints.
 */
export function useBreakpoint() {
  const isMobile = useMediaQuery('(max-width: 639px)');
  const isTablet = useMediaQuery('(min-width: 640px) and (max-width: 1023px)');
  const isDesktop = useMediaQuery('(min-width: 1024px)');
  const isLargeDesktop = useMediaQuery('(min-width: 1280px)');

  return useMemo(
    () => ({
      isMobile,
      isTablet,
      isDesktop,
      isLargeDesktop,
      breakpoint: isLargeDesktop ? 'xl' : isDesktop ? 'lg' : isTablet ? 'md' : 'sm',
    }),
    [isMobile, isTablet, isDesktop, isLargeDesktop]
  );
}

/**
 * Hook for intersection observer.
 */
export function useIntersectionObserver<T extends HTMLElement>(
  options?: IntersectionObserverInit
): [React.RefObject<T | null>, boolean] {
  const ref = useRef<T>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry?.isIntersecting ?? false);
    }, options);

    observer.observe(element);
    return () => observer.disconnect();
  }, [options]);

  return [ref, isIntersecting];
}

/**
 * Hook for previous value.
 */
export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T | undefined>(undefined);

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}

/**
 * Hook for async operation with loading state.
 */
export function useAsync<T, Args extends unknown[]>(
  asyncFn: (...args: Args) => Promise<T>
): {
  execute: (...args: Args) => Promise<T | undefined>;
  loading: boolean;
  error: Error | null;
  data: T | null;
} {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = useCallback(
    async (...args: Args) => {
      setLoading(true);
      setError(null);

      try {
        const result = await asyncFn(...args);
        setData(result);
        return result;
      } catch (e) {
        setError(e instanceof Error ? e : new Error(String(e)));
        return undefined;
      } finally {
        setLoading(false);
      }
    },
    [asyncFn]
  );

  return { execute, loading, error, data };
}

/**
 * Hook for clipboard operations.
 */
export function useClipboard(): {
  copy: (text: string) => Promise<boolean>;
  copied: boolean;
} {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      return true;
    } catch {
      return false;
    }
  }, []);

  return { copy, copied };
}
