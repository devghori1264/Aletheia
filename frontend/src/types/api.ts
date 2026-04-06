/**
 * API Types
 *
 * Type definitions for API requests and responses.
 * Strictly typed for type safety across the application.
 */

// =============================================================================
// Base Types
// =============================================================================

/** API response wrapper */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: Record<string, string[]>;
  meta?: ResponseMeta;
}

/** Pagination metadata */
export interface ResponseMeta {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

/** Pagination request params */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
  ordering?: string;
}

// =============================================================================
// Analysis Types
// =============================================================================

/** Analysis status enum */
export type AnalysisStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

/** Detection result */
export type DetectionResult = 'real' | 'fake' | 'uncertain';

/** Confidence level */
export type ConfidenceLevel = 'low' | 'medium' | 'high' | 'very_high';

/** Analysis request */
export interface AnalysisRequest {
  file?: File;
  url?: string;
  models?: string[];
  options?: AnalysisOptions;
}

/** Analysis options */
export interface AnalysisOptions {
  useEnsemble?: boolean;
  generateHeatmaps?: boolean;
  extractFrames?: boolean;
  frameInterval?: number;
  webhookUrl?: string;
}

/** Analysis response */
export interface Analysis {
  id: string;
  status: AnalysisStatus;
  prediction: DetectionResult | null;
  confidence: number | null;
  confidenceLevel: ConfidenceLevel | null;
  progress: number;
  mediaFile: MediaFile;
  modelResults: ModelResult[];
  frames: AnalysisFrame[];
  startedAt: string | null;
  completedAt: string | null;
  processingTime: number | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

/** Analysis summary (for list views) */
export interface AnalysisSummary {
  id: string;
  status: AnalysisStatus;
  prediction: DetectionResult | null;
  confidence: number | null;
  thumbnailUrl: string | null;
  fileName: string;
  createdAt: string;
}

/** Model-specific result */
export interface ModelResult {
  modelName: string;
  modelVersion: string;
  prediction: DetectionResult;
  confidence: number;
  fakeScore: number;
  realScore: number;
  processingTime: number;
  features?: Record<string, number>;
}

/** Analyzed frame */
export interface AnalysisFrame {
  frameNumber: number;
  timestamp: number;
  prediction: DetectionResult;
  confidence: number;
  fakeScore: number;
  imageUrl: string;
  heatmapUrl: string | null;
  faceDetected: boolean;
  faceBoundingBox: BoundingBox | null;
}

/** Bounding box */
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

// =============================================================================
// Media Types
// =============================================================================

/** Media file */
export interface MediaFile {
  id: string;
  fileName: string;
  fileSize: number;
  mimeType: string;
  duration: number | null;
  width: number | null;
  height: number | null;
  frameRate: number | null;
  thumbnailUrl: string | null;
  createdAt: string;
}

/** Upload progress */
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// =============================================================================
// Report Types
// =============================================================================

/** Report format */
export type ReportFormat = 'pdf' | 'json' | 'csv';

/** Report request */
export interface ReportRequest {
  analysisId: string;
  format: ReportFormat;
  includeFrames?: boolean;
  includeHeatmaps?: boolean;
  includeMetadata?: boolean;
}

/** Report response */
export interface Report {
  id: string;
  analysisId: string;
  format: ReportFormat;
  downloadUrl: string;
  generatedAt: string;
  expiresAt: string;
}

// =============================================================================
// Batch Types
// =============================================================================

/** Batch job */
export interface BatchJob {
  id: string;
  status: AnalysisStatus;
  totalItems: number;
  completedItems: number;
  failedItems: number;
  items: BatchItem[];
  createdAt: string;
  completedAt: string | null;
}

/** Batch item */
export interface BatchItem {
  id: string;
  analysisId: string | null;
  fileName: string;
  status: AnalysisStatus;
  prediction: DetectionResult | null;
  confidence: number | null;
  error: string | null;
}

// =============================================================================
// Model Types
// =============================================================================

/** Available model */
export interface ModelInfo {
  name: string;
  displayName: string;
  version: string;
  description: string;
  architecture: string;
  parameters: number;
  accuracy: number;
  latency: number;
  isDefault: boolean;
  isAvailable: boolean;
}

// =============================================================================
// Health Types
// =============================================================================

/** Health status */
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  uptime: number;
  services: ServiceHealth[];
  models: ModelHealth[];
}

/** Service health */
export interface ServiceHealth {
  name: string;
  status: 'up' | 'down' | 'degraded';
  latency: number | null;
  message: string | null;
}

/** Model health */
export interface ModelHealth {
  name: string;
  loaded: boolean;
  memory: number;
  device: string;
}

// =============================================================================
// WebSocket Types
// =============================================================================

/** WebSocket message types */
export type WSMessageType =
  | 'analysis_started'
  | 'analysis_progress'
  | 'analysis_completed'
  | 'analysis_failed'
  | 'frame_processed'
  | 'error';

/** WebSocket message */
export interface WSMessage<T = unknown> {
  type: WSMessageType;
  analysisId: string;
  data: T;
  timestamp: string;
}

/** Progress update */
export interface ProgressUpdate {
  progress: number;
  stage: string;
  message: string;
  framesProcessed?: number;
  totalFrames?: number;
}

// =============================================================================
// Error Types
// =============================================================================

/** API error */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  field?: string;
}

/** Validation error */
export interface ValidationError {
  field: string;
  message: string;
  code: string;
}
