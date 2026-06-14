import client from './client';
import type { Dataset, CreateDatasetRequest } from '../types';

export const datasetsApi = {
  list(): Promise<Dataset[]> {
    return client.get('/datasets').then((r) => r.data.items ?? r.data);
  },

  get(id: string): Promise<Dataset> {
    return client.get(`/datasets/${id}`).then((r) => r.data);
  },

  create(data: CreateDatasetRequest): Promise<Dataset> {
    return client.post('/datasets', data).then((r) => r.data);
  },

  update(id: string, data: Partial<CreateDatasetRequest>): Promise<Dataset> {
    return client.put(`/datasets/${id}`, data).then((r) => r.data);
  },

  delete(id: string): Promise<void> {
    return client.delete(`/datasets/${id}`);
  },
};
