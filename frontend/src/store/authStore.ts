import { create } from 'zustand';
import type { User } from '../types';
import { authApi } from '../api/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  initialized: boolean;

  setAuth: (user: User, token: string) => void;
  logout: () => void;
  initialize: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  loading: false,
  initialized: false,

  setAuth: (user, token) => {
    localStorage.setItem('accessToken', token);
    localStorage.setItem('user', JSON.stringify(user));
    set({ user, token, initialized: true });
  },

  logout: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    set({ user: null, token: null });
  },

  initialize: async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      set({ initialized: true });
      return;
    }
    try {
      const user = await authApi.getMe();
      set({ user, token, initialized: true });
    } catch {
      // token 清除由 axios 401 拦截器处理（硬跳转 /login）
      // 网络错误等非 401 场景保留 token，避免一刷新就被踢回登录页
      set({ user: null, initialized: true });
    }
  },

  login: async (username, password) => {
    set({ loading: true });
    try {
      const res = await authApi.login({ username, password });
      get().setAuth(res.user, res.accessToken);
    } finally {
      set({ loading: false });
    }
  },

  register: async (username, email, password) => {
    set({ loading: true });
    try {
      await authApi.register({ username, email, password });
    } finally {
      set({ loading: false });
    }
  },
}));
