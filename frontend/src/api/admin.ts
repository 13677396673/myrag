import client from './client';
import type { User, AdminStats } from '../types';

export const adminApi = {
  getUsers(): Promise<User[]> {
    return client.get('/admin/users').then((r) => r.data);
  },

  getStats(): Promise<AdminStats> {
    return client.get('/admin/stats').then((r) => r.data);
  },
};
