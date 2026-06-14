import client from './client';
import type {
  Conversation,
  CreateConversationRequest,
  Message,
  SendMessageRequest,
} from '../types';

export const conversationsApi = {
  list(): Promise<Conversation[]> {
    return client.get('/conversations').then((r) => r.data.items ?? r.data);
  },

  get(id: string): Promise<Conversation> {
    return client.get(`/conversations/${id}`).then((r) => r.data);
  },

  create(data: CreateConversationRequest): Promise<Conversation> {
    return client.post('/conversations', data).then((r) => r.data);
  },

  delete(id: string): Promise<void> {
    return client.delete(`/conversations/${id}`);
  },

  getMessages(id: string): Promise<Message[]> {
    return client.get(`/conversations/${id}/messages`).then((r) => r.data.items ?? r.data);
  },

  /** 发送消息并返回 SSE 响应 URL（用于 EventSource / fetch 流式读取） */
  sendMessage(id: string, data: SendMessageRequest): Promise<Response> {
    const token = localStorage.getItem('accessToken');
    return fetch(`/api/v1/conversations/${id}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
  },
};
