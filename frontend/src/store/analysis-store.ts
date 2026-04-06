/**
 * Analysis Store
 *
 * Global state management for analysis operations using Zustand.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Analysis, AnalysisSummary, UploadProgress } from '@/types/api';

// =============================================================================
// Types
// =============================================================================

interface AnalysisState {
  // Current analysis
  currentAnalysis: Analysis | null;
  currentProgress: UploadProgress | null;

  // Upload state
  uploadQueue: File[];
  isUploading: boolean;
  uploadError: string | null;

  // History
  recentAnalyses: AnalysisSummary[];
  historyLoaded: boolean;

  // UI state
  selectedFrameIndex: number | null;
  showHeatmaps: boolean;
  comparisonMode: boolean;
}

interface AnalysisActions {
  // Analysis actions
  setCurrentAnalysis: (analysis: Analysis | null) => void;
  updateAnalysisProgress: (progress: Partial<Analysis>) => void;
  clearCurrentAnalysis: () => void;

  // Upload actions
  addToUploadQueue: (files: File[]) => void;
  removeFromUploadQueue: (index: number) => void;
  clearUploadQueue: () => void;
  setIsUploading: (isUploading: boolean) => void;
  setUploadProgress: (progress: UploadProgress | null) => void;
  setUploadError: (error: string | null) => void;

  // History actions
  setRecentAnalyses: (analyses: AnalysisSummary[]) => void;
  addToRecentAnalyses: (analysis: AnalysisSummary) => void;
  removeFromRecentAnalyses: (id: string) => void;

  // UI actions
  setSelectedFrameIndex: (index: number | null) => void;
  setShowHeatmaps: (show: boolean) => void;
  setComparisonMode: (enabled: boolean) => void;

  // Reset
  reset: () => void;
}

type AnalysisStore = AnalysisState & AnalysisActions;

// =============================================================================
// Initial State
// =============================================================================

const initialState: AnalysisState = {
  currentAnalysis: null,
  currentProgress: null,
  uploadQueue: [],
  isUploading: false,
  uploadError: null,
  recentAnalyses: [],
  historyLoaded: false,
  selectedFrameIndex: null,
  showHeatmaps: false,
  comparisonMode: false,
};

// =============================================================================
// Store
// =============================================================================

export const useAnalysisStore = create<AnalysisStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Analysis actions
        setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),

        updateAnalysisProgress: (progress) =>
          set((state) => ({
            currentAnalysis: state.currentAnalysis
              ? { ...state.currentAnalysis, ...progress }
              : null,
          })),

        clearCurrentAnalysis: () =>
          set({
            currentAnalysis: null,
            currentProgress: null,
            selectedFrameIndex: null,
          }),

        // Upload actions
        addToUploadQueue: (files) =>
          set((state) => ({
            uploadQueue: [...state.uploadQueue, ...files],
          })),

        removeFromUploadQueue: (index) =>
          set((state) => ({
            uploadQueue: state.uploadQueue.filter((_, i) => i !== index),
          })),

        clearUploadQueue: () => set({ uploadQueue: [] }),

        setIsUploading: (isUploading) => set({ isUploading }),

        setUploadProgress: (progress) => set({ currentProgress: progress }),

        setUploadError: (error) => set({ uploadError: error }),

        // History actions
        setRecentAnalyses: (analyses) =>
          set({
            recentAnalyses: analyses,
            historyLoaded: true,
          }),

        addToRecentAnalyses: (analysis) =>
          set((state) => ({
            recentAnalyses: [
              analysis,
              ...state.recentAnalyses.filter((a) => a.id !== analysis.id),
            ].slice(0, 50), // Keep last 50
          })),

        removeFromRecentAnalyses: (id) =>
          set((state) => ({
            recentAnalyses: state.recentAnalyses.filter((a) => a.id !== id),
          })),

        // UI actions
        setSelectedFrameIndex: (index) => set({ selectedFrameIndex: index }),

        setShowHeatmaps: (show) => set({ showHeatmaps: show }),

        setComparisonMode: (enabled) => set({ comparisonMode: enabled }),

        // Reset
        reset: () => set(initialState),
      }),
      {
        name: 'aletheia-analysis',
        partialize: (state) => ({
          recentAnalyses: state.recentAnalyses,
          historyLoaded: state.historyLoaded,
          showHeatmaps: state.showHeatmaps,
        }),
      }
    ),
    { name: 'AnalysisStore' }
  )
);

// =============================================================================
// Selectors
// =============================================================================

export const selectCurrentAnalysis = (state: AnalysisStore) => state.currentAnalysis;
export const selectUploadQueue = (state: AnalysisStore) => state.uploadQueue;
export const selectIsUploading = (state: AnalysisStore) => state.isUploading;
export const selectRecentAnalyses = (state: AnalysisStore) => state.recentAnalyses;
export const selectSelectedFrameIndex = (state: AnalysisStore) => state.selectedFrameIndex;
export const selectShowHeatmaps = (state: AnalysisStore) => state.showHeatmaps;
