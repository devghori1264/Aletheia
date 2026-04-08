/**
 * Analysis Service
 *
 * API service for analysis-related operations.
 */

import { apiClient } from './api-client';
import type {
  Analysis,
  AnalysisSummary,
  AnalysisRequest,
  AnalysisOptions,
  Report,
  ReportFormat,
  PaginationParams,
  ResponseMeta,
} from '@/types/api';

// =============================================================================
// Types
// =============================================================================

interface AnalysisListResponse {
  items: AnalysisSummary[];
  meta: ResponseMeta;
}

interface CreateAnalysisResponse {
  analysis: Analysis;
  uploadUrl?: string;
}

// =============================================================================
// Analysis Service
// =============================================================================

export const analysisService = {
  /**
   * Get analysis list with pagination.
   */
  async getList(params?: PaginationParams): Promise<AnalysisListResponse> {
    return apiClient.get<AnalysisListResponse>('/analysis/', { params });
  },

  /**
   * Get analysis by ID.
   */
  async getById(id: string): Promise<Analysis> {
    return apiClient.get<Analysis>(`/analysis/${id}/`);
  },

  /**
   * Create new analysis by uploading a file.
   */
  async create(
    file: File,
    options?: AnalysisOptions,
    onProgress?: (progress: number) => void
  ): Promise<Analysis> {
    const config = options ? {
      use_ensemble: options.useEnsemble ?? true,
      generate_heatmaps: options.generateHeatmaps ?? true,
      sequence_length: options.frameInterval ?? 60,
      model_name: 'ensemble',
      webhook_url: options.webhookUrl ?? '',
    } : undefined;
    
    return apiClient.upload<Analysis>('/analysis/submit/', file, onProgress, {
      config: config ? JSON.stringify(config) : '',
    });
  },

  /**
   * Create analysis from URL.
   */
  async createFromUrl(url: string, options?: AnalysisOptions): Promise<Analysis> {
    return apiClient.post<Analysis>('/analysis/url/', {
      url,
      options,
    });
  },

  /**
   * Cancel a running analysis.
   */
  async cancel(id: string): Promise<void> {
    return apiClient.post(`/analysis/${id}/cancel/`);
  },

  /**
   * Delete an analysis.
   */
  async delete(id: string): Promise<void> {
    return apiClient.delete(`/analysis/${id}/`);
  },

  /**
   * Retry a failed analysis.
   */
  async retry(id: string): Promise<Analysis> {
    return apiClient.post<Analysis>(`/analysis/${id}/retry/`);
  },

  /**
   * Get analysis frames.
   */
  async getFrames(id: string): Promise<Analysis['frames']> {
    return apiClient.get<Analysis['frames']>(`/analysis/${id}/frames/`);
  },

  /**
   * Generate report.
   */
  async generateReport(
    analysisId: string,
    format: ReportFormat,
    options?: { includeFrames?: boolean; includeHeatmaps?: boolean }
  ): Promise<Report> {
    return apiClient.post<Report>(`/analysis/${analysisId}/report/`, {
      format,
      ...options,
    });
  },

  /**
   * Download report.
   */
  async downloadReport(analysisId: string, format: ReportFormat): Promise<void> {
    const report = await this.generateReport(analysisId, format);
    await apiClient.download(report.downloadUrl, `analysis-${analysisId}.${format}`);
  },

  /**
   * Get analysis statistics.
   */
  async getStats(): Promise<{
    totalAnalyses: number;
    fakeDetected: number;
    realDetected: number;
    averageConfidence: number;
    averageProcessingTime: number;
  }> {
    return apiClient.get('/analysis/stats/');
  },
};

// =============================================================================
// React Query Keys
// =============================================================================

export const analysisKeys = {
  all: ['analysis'] as const,
  lists: () => [...analysisKeys.all, 'list'] as const,
  list: (params: PaginationParams) => [...analysisKeys.lists(), params] as const,
  details: () => [...analysisKeys.all, 'detail'] as const,
  detail: (id: string) => [...analysisKeys.details(), id] as const,
  frames: (id: string) => [...analysisKeys.detail(id), 'frames'] as const,
  stats: () => [...analysisKeys.all, 'stats'] as const,
};
