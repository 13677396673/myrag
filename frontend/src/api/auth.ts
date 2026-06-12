import client from './client';
import type { LoginRequest, LoginResponse, RegisterRequest, User } from '../types';

export const authApi = {
  login(data: LoginRequest): Promise<LoginResponse> {
    return client.post('/auth/login', data).then((r) => r.data);
  },

  register(data: RegisterRequest): Promise<User> {
    return client.post('/auth/register', data).then((r) => r.data);
  },

  getMe(): Promise<User> {
    return client.get('/users/me').then((r) => r.data);
  },

  updateProfile(data: Partial<User>): Promise<User> {
    return client.put('/users/me', data).then((r) => r.data);
  },

  changePassword(data: { oldPassword: string; newPassword: string }): Promise<{ message: string }> {
    return client.put('/users/me/password', data).then((r) => r.data);
  },
};
