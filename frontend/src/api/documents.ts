import client from './client';
import type { Document } from '../types';

export const documentsApi = {
  list(datasetId: string): Promise<Document[]> {
    return client.get(`/datasets/${datasetId}/documents`).then((r) => r.data);
  },

  upload(datasetId: string, file: File, onProgress?: (percent: number) => void): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    return client
      .post(`/datasets/${datasetId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (onProgress && e.total) {
            onProgress(Math.round((e.loaded / e.total) * 100));
          }
        },
      })
      .then((r) => r.data);
  },

  get(id: string): Promise<Document> {
    return client.get(`/documents/${id}`).then((r) => r.data);
  },

  getStatus(id: string): Promise<Document> {
    return client.get(`/documents/${id}/status`).then((r) => r.data);
  },

  delete(id: string): Promise<void> {
    return client.delete(`/documents/${id}`);
  },
};
