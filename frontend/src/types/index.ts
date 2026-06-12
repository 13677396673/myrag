// ===== 通用类型 =====

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// ===== 用户 / 认证 =====

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'user' | 'admin';
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  tokenType?: string;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken?: string;
  user: User;
}

// ===== 数据集 =====

export interface Dataset {
  id: string;
  name: string;
  description: string;
  documentCount: number;
  chunkCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateDatasetRequest {
  name: string;
  description?: string;
}

// ===== 文档 =====

export type DocumentStatus = 'pending' | 'parsing' | 'completed' | 'failed';

export interface Document {
  id: string;
  datasetId: string;
  filename: string;
  fileType: string;
  fileSize: number;
  status: DocumentStatus;
  chunkCount: number;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

// ===== 对话 / 消息 =====

export interface Conversation {
  id: string;
  title: string;
  datasetId?: string;
  datasetName?: string;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateConversationRequest {
  title?: string;
  datasetId?: string;
}

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceReference[];
  createdAt: string;
}

export interface SourceReference {
  documentId: string;
  documentName: string;
  chunkId: string;
  content: string;
  score: number;
}

export interface SendMessageRequest {
  content: string;
  datasetId?: string;
  stream?: boolean;
}

// ===== SSE 事件 =====

export interface SSEChunkEvent {
  type: 'chunk';
  content: string;
}

export interface SSESourceEvent {
  type: 'source';
  sources: SourceReference[];
}

export interface SSEErrorEvent {
  type: 'error';
  message: string;
}

export interface SSEDoneEvent {
  type: 'done';
}

export type SSEEvent = SSEChunkEvent | SSESourceEvent | SSEErrorEvent | SSEDoneEvent;

// ===== 管理后台 =====

export interface AdminStats {
  totalUsers: number;
  totalDatasets: number;
  totalDocuments: number;
  totalConversations: number;
  totalMessages: number;
}
