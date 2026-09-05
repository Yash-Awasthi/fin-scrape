/**
 * Enhanced API client with interceptors, retry logic, and caching
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

// Types
export interface APIConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
  withCredentials?: boolean;
  retryAttempts?: number;
  retryDelay?: number;
}

export interface APIError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
  timestamp: Date;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  requestId?: string;
  timestamp: Date;
}

// Cache implementation
class SimpleCache {
  private cache: Map<string, { data: any; expiry: number }> = new Map();

  set(key: string, data: any, ttl: number = 300000): void {
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl
    });
  }

  get(key: string): any | null {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(pattern: string): void {
    const keys = Array.from(this.cache.keys());
    keys.forEach(key => {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    });
  }
}

// API Client Class
export class APIClient {
  private client: AxiosInstance;
  private cache: SimpleCache;
  private retryAttempts: number;
  private retryDelay: number;
  private requestQueue: Map<string, Promise<any>> = new Map();

  constructor(config: APIConfig) {
    this.retryAttempts = config.retryAttempts ?? 3;
    this.retryDelay = config.retryDelay ?? 1000;
    this.cache = new SimpleCache();

    // Create axios instance
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout ?? 30000,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers
      },
      withCredentials: config.withCredentials ?? false
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request ID
        config.headers['X-Request-ID'] = this.generateRequestId();

        // Log request in development
        if (import.meta.env.DEV) {
          console.log('API Request:', {
            method: config.method,
            url: config.url,
            params: config.params,
            data: config.data
          });
        }

        return config;
      },
      (error) => {
        return Promise.reject(this.handleError(error));
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Log response in development
        if (import.meta.env.DEV) {
          console.log('API Response:', {
            status: response.status,
            url: response.config.url,
            data: response.data
          });
        }

        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Retry logic
        if (this.shouldRetry(error) && !originalRequest._retry) {
          originalRequest._retry = true;
          originalRequest._retryCount = (originalRequest._retryCount ?? 0) + 1;

          if (originalRequest._retryCount <= this.retryAttempts) {
            await this.delay(this.retryDelay * originalRequest._retryCount);
            return this.client(originalRequest);
          }
        }

        // Handle 401 - Unauthorized
        if (error.response?.status === 401) {
          this.handleUnauthorized();
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  private shouldRetry(error: AxiosError): boolean {
    // Retry on network errors or 5xx errors
    return !error.response || (error.response.status >= 500 && error.response.status < 600);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private getAuthToken(): string | null {
    // Get from localStorage or sessionStorage
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  }

  private handleUnauthorized(): void {
    // Clear auth and redirect to login
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
    window.location.href = '/login';
  }

  private handleError(error: AxiosError): APIError {
    const apiError: APIError = {
      message: 'An unexpected error occurred',
      timestamp: new Date()
    };

    if (error.response) {
      // Server responded with error
      const data = error.response.data as Record<string, unknown> | undefined;
      apiError.status = error.response.status;
      apiError.message = (data?.message as string) || error.message;
      apiError.code = data?.code as string | undefined;
      apiError.details = data?.details;
    } else if (error.request) {
      // Request made but no response
      apiError.message = 'No response from server';
      apiError.code = 'NETWORK_ERROR';
    } else {
      // Request setup error
      apiError.message = error.message;
      apiError.code = 'REQUEST_ERROR';
    }

    return apiError;
  }

  private getCacheKey(method: string, url: string, params?: any): string {
    return `${method}:${url}:${JSON.stringify(params || {})}`;
  }

  // HTTP Methods with caching
  async get<T = any>(
    url: string, 
    config?: AxiosRequestConfig & { cache?: boolean; cacheTTL?: number }
  ): Promise<T> {
    const cacheKey = this.getCacheKey('GET', url, config?.params);
    
    // Check cache
    if (config?.cache !== false) {
      const cached = this.cache.get(cacheKey);
      if (cached) return cached;
    }

    // Check if request is already in progress
    const existingRequest = this.requestQueue.get(cacheKey);
    if (existingRequest) {
      return existingRequest;
    }

    // Make request
    const requestPromise = this.client.get<T>(url, config).then(response => {
      const data = response.data;
      
      // Cache successful response
      if (config?.cache !== false) {
        this.cache.set(cacheKey, data, config?.cacheTTL);
      }
      
      this.requestQueue.delete(cacheKey);
      return data;
    }).catch(error => {
      this.requestQueue.delete(cacheKey);
      throw error;
    });

    this.requestQueue.set(cacheKey, requestPromise);
    return requestPromise;
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    // Invalidate related cache
    this.cache.delete(url);
    return response.data;
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    // Invalidate related cache
    this.cache.delete(url);
    return response.data;
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    // Invalidate related cache
    this.cache.delete(url);
    return response.data;
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    // Invalidate related cache
    this.cache.delete(url);
    return response.data;
  }

  // Utility methods
  clearCache(): void {
    this.cache.clear();
  }

  setAuthToken(token: string, persist: boolean = true): void {
    if (persist) {
      localStorage.setItem('auth_token', token);
    } else {
      sessionStorage.setItem('auth_token', token);
    }
  }

  removeAuthToken(): void {
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
  }

  // Paginated request helper
  async getPaginated<T>(
    url: string,
    page: number = 1,
    pageSize: number = 20,
    params?: any
  ): Promise<PaginatedResponse<T>> {
    return this.get<PaginatedResponse<T>>(url, {
      params: {
        page,
        page_size: pageSize,
        ...params
      }
    });
  }
}

// Create default instance
const apiClient = new APIClient({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  withCredentials: true
});

export default apiClient;