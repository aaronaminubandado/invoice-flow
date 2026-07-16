import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const publicApi = axios.create({
  baseURL: API_BASE_URL,
})

export interface PublicInvoice {
  invoice_number: string | null
  status: string
  description: string | null
  due_date: string
  created_at: string | null
  amount: string
  paid_amount: string
  balance_due: string
  client_name: string
  business: {
    business_name: string
    business_email: string
    phone?: string
    address?: string
    currency: string
  } | null
  items: Array<{
    id: string
    position: number
    description: string
    quantity: string
    unit_price: string
    line_total: string
  }>
}

export const publicInvoicesApi = {
  get: async (token: string) => {
    const { data } = await publicApi.get<PublicInvoice>(`/public/invoices/${token}`)
    return data
  },

  downloadPdf: async (token: string) => {
    const response = await publicApi.get(`/public/invoices/${token}/pdf`, {
      responseType: 'blob',
    })
    return response.data as Blob
  },
}
