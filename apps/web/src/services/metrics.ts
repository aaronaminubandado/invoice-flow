import { api } from '@/lib/axios'
import { RevenueSummary, MonthlyRevenue } from '@/types'
import type { ExportFormat } from './invoices'

export const metricsApi = {
  getRevenueSummary: async () => {
    const { data } = await api.get<RevenueSummary>('/metrics/revenue-summary')
    return data
  },

  getMonthlyRevenue: async () => {
    const { data } = await api.get<MonthlyRevenue[]>('/metrics/monthly-revenue')
    return data
  },

  export: async (format: ExportFormat = 'csv') => {
    const response = await api.get(`/metrics/export?format=${format}`, {
      responseType: 'blob',
    })
    return response.data
  },
}
