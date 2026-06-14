import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ── 工具：递归将 snake_case 对象的 key 转为 camelCase ──
function toCamelCase<T>(obj: T): T {
  if (Array.isArray(obj)) {
    return obj.map(toCamelCase) as unknown as T;
  }
  if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj as Record<string, unknown>).reduce(
      (acc, key) => {
        const camelKey = key.replace(/_([a-z])/g, (_, c: string) =>
          c.toUpperCase(),
        );
        (acc as Record<string, unknown>)[camelKey] = toCamelCase(
          (obj as Record<string, unknown>)[key],
        );
        return acc;
      },
      {} as Record<string, unknown>,
    ) as T;
  }
  return obj;
}

// ── 请求拦截器：自动携带 Token ──
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('accessToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ── 响应拦截器：解包 ApiResponse + snake_case 转 camelCase ──
client.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data === 'object') {
      let data = response.data;
      // 解包后端统一的 ApiResponse 格式：{ code, message, data: actualData }
      if ('code' in data && 'data' in data && !Array.isArray(data)) {
        data = data.data;
      }
      // snake_case → camelCase
      response.data = toCamelCase(data);
    }
    return response;
  },
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('user');
      // 未登录时跳转到登录页（使用事件而非硬跳转，避免与 React Router 冲突）
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    }
    const message =
      error.response?.data?.detail || error.message || '请求失败，请稍后重试';
    return Promise.reject(new Error(message));
  },
);

export default client;
