import { api } from '@/lib/axios'
import { Client, CreateClientInput, PaginatedResponse } from '@/types'
import type { ExportFormat } from '@/lib/download'

export const clientsApi = {
  list: async (params?: { limit?: number; offset?: number }) => {
    const { data } = await api.get<PaginatedResponse<Client>>('/clients', {
      params,
    })
    return data
  },

  get: async (id: string) => {
    const { data } = await api.get<Client>(`/clients/${id}`)
    return data
  },

  create: async (input: CreateClientInput) => {
    const { data } = await api.post<Client>('/clients', input)
    return data
  },

  update: async (id: string, input: Partial<CreateClientInput>) => {
    const { data } = await api.put<Client>(`/clients/${id}`, input)
    return data
  },

  delete: async (id: string) => {
    await api.delete(`/clients/${id}`)
  },

  export: async (format: ExportFormat = 'csv') => {
    const response = await api.get(`/clients/export?format=${format}`, {
      responseType: 'blob',
    })
    return response.data
  },
}
