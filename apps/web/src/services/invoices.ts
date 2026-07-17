import { api } from '@/lib/axios'
import {
  Invoice,
  CreateInvoiceInput,
  CreatePaymentInput,
  Payment,
  InvoiceWithPayments,
  PaginatedResponse,
} from '@/types'
import type { ExportFormat } from '@/lib/download'

export type { ExportFormat }

export const invoicesApi = {
  list: async (params?: {
    limit?: number
    offset?: number
    status?: string
  }) => {
    const { data } = await api.get<PaginatedResponse<Invoice>>('/invoices', {
      params,
    })
    return data
  },

  get: async (id: string) => {
    const { data } = await api.get<Invoice>(`/invoices/${id}`)
    return data
  },

  create: async (input: CreateInvoiceInput) => {
    const { data } = await api.post<Invoice>('/invoices', input)
    return data
  },

  send: async (id: string) => {
    const { data } = await api.post<Invoice>(`/invoices/${id}/send`)
    return data
  },

  update: async (id: string, input: Partial<CreateInvoiceInput>) => {
    const { data } = await api.put<Invoice>(`/invoices/${id}`, input)
    return data
  },

  delete: async (id: string) => {
    await api.delete(`/invoices/${id}`)
  },

  cancel: async (id: string) => {
    const { data } = await api.post<{ message: string; status: string }>(
      `/invoices/${id}/cancel`
    )
    return data
  },

  resend: async (id: string) => {
    const { data } = await api.post<{ message: string }>(`/invoices/${id}/resend`)
    return data
  },

  markPaid: async (id: string) => {
    const { data } = await api.post<Invoice>(`/invoices/${id}/mark-paid`)
    return data
  },

  addPayment: async (id: string, input: CreatePaymentInput) => {
    const { data } = await api.post<InvoiceWithPayments>(
      `/invoices/${id}/payments`,
      input
    )
    return data
  },

  getPayments: async (invoiceId: string) => {
    const { data } = await api.get<Payment[]>(`/invoices/${invoiceId}/payments`)
    return data
  },

  downloadPdf: async (id: string) => {
    const response = await api.get(`/invoices/${id}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  },

  downloadReceipt: async (invoiceId: string, paymentId: string) => {
    const response = await api.get(
      `/invoices/${invoiceId}/payments/${paymentId}/receipt`,
      { responseType: 'blob' }
    )
    return response.data
  },

  export: async (format: ExportFormat = 'csv') => {
    const response = await api.get(`/invoices/export?format=${format}`, {
      responseType: 'blob',
    })
    return response.data
  },
}
