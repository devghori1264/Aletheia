/**
 * API Client
 *
 * Configured Axios instance for API communication.
 * Includes interceptors for auth, error handling, and request/response transformation.
 */

import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
  AxiosError,
} from 'axios';
import type { ApiResponse, ApiError } from '@/types/api';

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
const API_TIMEOUT = 300000; // 5 minutes — analysis of large videos runs synchronously

// =============================================================================
// Custom Error Class
// =============================================================================

export class ApiClientError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly details?: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.status = status;
    this.details = details;
  }

  static fromAxiosError(error: AxiosError<ApiError>): ApiClientError {
    const status = error.response?.status || 0;
    const data = error.response?.data;

    if (data) {
      return new ApiClientError(
        data.message || error.message,
        data.code || 'UNKNOWN_ERROR',
        status,
        data.details
      );
    }

    // Network errors
    if (error.code === 'ECONNABORTED') {
      return new ApiClientError('Request timed out', 'TIMEOUT', 0);
    }

    if (!error.response) {
      return new ApiClientError('Network error', 'NETWORK_ERROR', 0);
    }

    return new ApiClientError(error.message, 'UNKNOWN_ERROR', status);
  }
}

// =============================================================================
// API Client Class
// =============================================================================

class ApiClient {
  private readonly instance: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    this.instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      withCredentials: false, // Don't send cookies - avoids CSRF issues
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Set up request and response interceptors.
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add auth token if available
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }

        // Add request timestamp for timing
        config.metadata = { startTime: Date.now() };

        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log response time in development
        if (import.meta.env.DEV) {
          const duration = Date.now() - (response.config.metadata?.startTime || 0);
          console.debug(
            `[API] ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`
          );
        }

        return response;
      },
      (error: AxiosError<ApiError>) => {
        // Handle specific error cases
        if (error.response?.status === 401) {
          // Clear auth token and redirect to login
          this.clearAuthToken();
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }

        throw ApiClientError.fromAxiosError(error);
      }
    );
  }

  /**
   * Set the authentication token.
   */
  setAuthToken(token: string): void {
    this.authToken = token;
  }

  /**
   * Clear the authentication token.
   */
  clearAuthToken(): void {
    this.authToken = null;
  }

  /**
   * GET request.
   */
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T | ApiResponse<T>>(url, config);
    // Handle both wrapped ({ data: ... }) and unwrapped responses
    const data = response.data as any;
    if (data && typeof data === 'object' && 'data' in data) {
      return data.data as T;
    }
    return data as T;
  }

  /**
   * POST request.
   */
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T | ApiResponse<T>>(url, data, config);
    // Handle both wrapped ({ data: ... }) and unwrapped responses
    const resData = response.data as any;
    if (resData && typeof resData === 'object' && 'data' in resData) {
      return resData.data as T;
    }
    return resData as T;
  }

  /**
   * PUT request.
   */
  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T | ApiResponse<T>>(url, data, config);
    const resData = response.data as any;
    if (resData && typeof resData === 'object' && 'data' in resData) {
      return resData.data as T;
    }
    return resData as T;
  }

  /**
   * PATCH request.
   */
  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.patch<T | ApiResponse<T>>(url, data, config);
    const resData = response.data as any;
    if (resData && typeof resData === 'object' && 'data' in resData) {
      return resData.data as T;
    }
    return resData as T;
  }

  /**
   * DELETE request.
   */
  async delete<T = void>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T | ApiResponse<T>>(url, config);
    const data = response.data as any;
    if (data && typeof data === 'object' && 'data' in data) {
      return data.data as T;
    }
    return data as T;
  }

  /**
   * Upload file with progress tracking.
   */
  async upload<T>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    additionalData?: Record<string, string>
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const response = await this.instance.post<T | ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentage);
        }
      },
    });

    // Handle both wrapped ({ data: ... }) and unwrapped responses
    const data = response.data as any;
    if (data && typeof data === 'object' && 'data' in data) {
      return data.data as T;
    }
    return data as T;
  }

  /**
   * Download file.
   */
  async download(url: string, filename: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob',
    });

    // Create download link
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  /**
   * Get the underlying Axios instance for advanced use cases.
   */
  getAxiosInstance(): AxiosInstance {
    return this.instance;
  }
}

// =============================================================================
// Export Singleton
// =============================================================================

export const apiClient = new ApiClient();

// Type augmentation for request config
declare module 'axios' {
  export interface AxiosRequestConfig {
    metadata?: {
      startTime: number;
    };
  }
}
