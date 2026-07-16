export interface Client {
  id: string
  user_id: string
  name: string
  email: string
  phone?: string
  address?: string
  created_at: string
}

export interface Invoice {
  id: string
  user_id: string
  client_id: string
  client?: Client
  amount: string
  description?: string
  due_date: string
  status: 'draft' | 'sent' | 'overdue' | 'paid' | 'partial' | 'cancelled' | 'void'
  created_at: string
  invoice_number?: string
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

export interface InvoiceWithPayments extends Invoice {
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

export interface CreateInvoiceInput {
  client_id: string
  amount: number
  due_date: string
  description?: string
}

export interface CreatePaymentInput {
  amount: number
  payment_method?: string
  payment_date?: string
  reference?: string
  notes?: string
}

export interface InvoiceStatusHistory {
  id: string
  invoice_id: string
  from_status: string | null
  to_status: string
  changed_at: string
  reason?: string
}
