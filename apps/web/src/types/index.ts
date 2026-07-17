export interface PaginatedResponse<T> {
  items: T[]
  total: number
}

export interface Client {
  id: string
  user_id?: string
  name: string
  email: string
  phone?: string
  address?: string
  created_at: string
}

export interface InvoiceItem {
  id?: string
  position?: number
  description: string
  quantity: number | string
  unit_price: number | string
  line_total?: number | string
}

export interface Invoice {
  id: string
  user_id: string
  client_id: string
  client_name?: string
  client_email?: string
  amount: string
  description?: string
  due_date: string
  status: 'draft' | 'sent' | 'overdue' | 'paid' | 'partial' | 'cancelled' | 'void'
  created_at: string
  invoice_number?: string
  share_token?: string
  items?: InvoiceItem[]
}

export interface Payment {
  id: string
  invoice_id: string
  amount: string
  payment_method: string
  payment_date: string
  reference?: string
  created_at: string
}

export interface InvoiceWithPayments {
  id: string
  amount: string
  status: string
  paid_amount?: string
  payments?: Payment[]
}

export interface RevenueSummary {
  total_revenue: string
  total_paid: string
  total_outstanding: string
  total_overdue: string
}

export interface MonthlyRevenue {
  month: string
  paid: string
  outstanding: string
}

export interface CreateClientInput {
  name: string
  email: string
  phone?: string
  address?: string
}

export interface CreateInvoiceItemInput {
  description: string
  quantity: number
  unit_price: number
}

export interface CreateInvoiceInput {
  client_id: string
  due_date: string
  description?: string
  amount?: number
  items?: CreateInvoiceItemInput[]
  send_now?: boolean
}

export interface CreatePaymentInput {
  amount: number
  payment_method?: string
  payment_date?: string
  reference?: string
  notes?: string
}
