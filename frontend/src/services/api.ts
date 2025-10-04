import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<TResponse>(url: string, config?: AxiosRequestConfig<unknown>): Promise<AxiosResponse<TResponse>> {
    return this.client.get<TResponse>(url, config);
  }

  async post<TResponse, TData = unknown>(
    url: string,
    data?: TData,
    config?: AxiosRequestConfig<TData>
  ): Promise<AxiosResponse<TResponse>> {
    return this.client.post<TResponse>(url, data, config);
  }

  async put<TResponse, TData = unknown>(
    url: string,
    data?: TData,
    config?: AxiosRequestConfig<TData>
  ): Promise<AxiosResponse<TResponse>> {
    return this.client.put<TResponse>(url, data, config);
  }

  async delete<TResponse>(url: string, config?: AxiosRequestConfig<unknown>): Promise<AxiosResponse<TResponse>> {
    return this.client.delete<TResponse>(url, config);
  }

  async patch<TResponse, TData = unknown>(
    url: string,
    data?: TData,
    config?: AxiosRequestConfig<TData>
  ): Promise<AxiosResponse<TResponse>> {
    return this.client.patch<TResponse>(url, data, config);
  }
}

export const apiClient = new ApiClient();