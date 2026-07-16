import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  Search,
  Eye,
  CreditCard,
  X,
  FileText,
  Download,
  Check,
  Send,
  Copy,
} from 'lucide-react'
import { format } from 'date-fns'
import {
  Button,
  Input,
  Card,
  CardContent,
  Badge,
  getStatusBadgeVariant,
  Modal,
  ConfirmDialog,
  Select,
  InvoiceCardSkeleton,
  ExportDropdown,
} from '@/components/ui'
import { useToast } from '@/components/ui/toast'
import { getErrorMessage } from '@/lib/axios'
import { formatCurrency } from '@/lib/utils'
import { invoicesApi, clientsApi } from '@/services'
import type { ExportFormat } from '@/services/invoices'
import {
  Invoice,
  Client,
  CreateInvoiceInput,
  CreatePaymentInput,
  CreateInvoiceItemInput,
  Payment,
} from '@/types'

const statusOptions = [
  { value: 'all', label: 'All Status' },
  { value: 'draft', label: 'Draft' },
  { value: 'sent', label: 'Sent' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'paid', label: 'Paid' },
  { value: 'partial', label: 'Partial' },
  { value: 'cancelled', label: 'Cancelled' },
]


const FILE_EXTENSIONS: Record<ExportFormat, string> = {
  csv: '.csv',
  xlsx: '.xlsx',
  pdf: '.pdf',
}

function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

export function InvoicesPage() {
  const queryClient = useQueryClient()
  const { success, error } = useToast()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [paymentModalOpen, setPaymentModalOpen] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)
  const [detailsInvoice, setDetailsInvoice] = useState<Invoice | null>(null)
  const [cancelConfirmOpen, setCancelConfirmOpen] = useState(false)
  const [invoiceToCancel, setInvoiceToCancel] = useState<string | null>(null)
  const [markPaidConfirmOpen, setMarkPaidConfirmOpen] = useState(false)
  const [invoiceToMarkPaid, setInvoiceToMarkPaid] = useState<string | null>(null)

  const { data: invoices, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: invoicesApi.list,
  })

  const { data: clients } = useQuery({
    queryKey: ['clients'],
    queryFn: clientsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: (input: CreateInvoiceInput) => invoicesApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setCreateModalOpen(false)
      success('Invoice created successfully')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const cancelMutation = useMutation({
    mutationFn: (id: string) => invoicesApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      success('Invoice cancelled successfully')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const paymentMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: CreatePaymentInput }) =>
      invoicesApi.addPayment(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setPaymentModalOpen(false)
      setSelectedInvoice(null)
      success('Payment recorded successfully')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const resendMutation = useMutation({
    mutationFn: (id: string) => invoicesApi.resend(id),
    onSuccess: () => success('Invoice email resent'),
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const markPaidMutation = useMutation({
    mutationFn: (id: string) => invoicesApi.markPaid(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      success('Invoice marked as paid')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const filteredInvoices = invoices?.filter((invoice) => {
    const matchesSearch =
      !search ||
      invoice.description?.toLowerCase().includes(search.toLowerCase()) ||
      invoice.invoice_number?.toLowerCase().includes(search.toLowerCase()) ||
      invoice.client_name?.toLowerCase().includes(search.toLowerCase())
    const matchesStatus = statusFilter === 'all' || invoice.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const handleExport = (fmt: ExportFormat) => {
    invoicesApi
      .export(fmt)
      .then((blob) => {
        const date = new Date().toISOString().split('T')[0]
        downloadBlob(blob, `invoices_${date}${FILE_EXTENSIONS[fmt]}`)
        success('Invoices exported successfully')
      })
      .catch(() => error('Failed to export invoices'))
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Invoices</h1>
          <p className="text-muted-foreground mt-1">
            Manage and track all your invoices
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ExportDropdown onExport={handleExport} />
          <Button onClick={() => setCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Invoice
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search invoices..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select
          options={statusOptions}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-40"
        />
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <InvoiceCardSkeleton />
          <InvoiceCardSkeleton />
          <InvoiceCardSkeleton />
        </div>
      ) : filteredInvoices?.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary">
            <FileText className="h-7 w-7 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-base font-semibold">No invoices found</h3>
          <p className="mt-1.5 text-sm text-muted-foreground max-w-[260px] text-center">
            {search || statusFilter !== 'all'
              ? 'Try adjusting your search or filters'
              : 'Create your first invoice to get started'}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence>
            {filteredInvoices?.map((invoice, index) => (
              <motion.div
                key={invoice.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ delay: index * 0.04 }}
              >
                <Card className="hover:border-primary/30 transition-colors group">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <Badge variant={getStatusBadgeVariant(invoice.status)}>
                        {invoice.status}
                      </Badge>
                      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => setDetailsInvoice(invoice)}
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                        {invoice.status !== 'paid' &&
                          invoice.status !== 'cancelled' && (
                            <>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7"
                                onClick={() => {
                                  setSelectedInvoice(invoice)
                                  setPaymentModalOpen(true)
                                }}
                              >
                                <CreditCard className="h-3.5 w-3.5" />
                              </Button>
                              {(invoice.status === 'sent' ||
                                invoice.status === 'overdue') && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-7 w-7"
                                  onClick={() => {
                                    setInvoiceToMarkPaid(invoice.id)
                                    setMarkPaidConfirmOpen(true)
                                  }}
                                >
                                  <Check className="h-3.5 w-3.5" />
                                </Button>
                              )}
                              {invoice.status !== 'overdue' &&
                                invoice.status !== 'partial' && (
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 text-destructive"
                                    onClick={() => {
                                      setInvoiceToCancel(invoice.id)
                                      setCancelConfirmOpen(true)
                                    }}
                                  >
                                    <X className="h-3.5 w-3.5" />
                                  </Button>
                                )}
                            </>
                          )}
                      </div>
                    </div>

                    <p className="text-sm font-medium truncate mb-1">
                      {invoice.client_name ?? 'Unknown client'}
                    </p>

                    <div className="flex items-baseline justify-between mb-1.5">
                      <span className="text-xl font-bold font-mono tabular-nums">
                        {formatCurrency(invoice.amount)}
                      </span>
                      <span className="text-xs font-mono text-muted-foreground">
                        {invoice.invoice_number || `#${invoice.id.slice(0, 8)}`}
                      </span>
                    </div>

                    <p className="text-sm text-muted-foreground truncate mb-3">
                      {invoice.description || 'No description'}
                    </p>

                    <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-border">
                      <span>
                        Due:{' '}
                        {invoice.due_date
                          ? format(new Date(invoice.due_date), 'MMM d, yyyy')
                          : 'N/A'}
                      </span>
                      <span>
                        {invoice.created_at
                          ? format(new Date(invoice.created_at), 'MMM d')
                          : 'N/A'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <CreateInvoiceModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        clients={clients || []}
        onSubmit={(data) => createMutation.mutate(data)}
        loading={createMutation.isPending}
      />

      <PaymentModal
        open={paymentModalOpen}
        onClose={() => {
          setPaymentModalOpen(false)
          setSelectedInvoice(null)
        }}
        invoice={selectedInvoice}
        onSubmit={(input) => {
          if (selectedInvoice) {
            paymentMutation.mutate({ id: selectedInvoice.id, input })
          }
        }}
        loading={paymentMutation.isPending}
      />

      <InvoiceDetailsDrawer
        open={!!detailsInvoice}
        onClose={() => setDetailsInvoice(null)}
        invoiceId={detailsInvoice?.id ?? null}
        onResend={(id: string) => resendMutation.mutate(id)}
      />

      <ConfirmDialog
        open={cancelConfirmOpen}
        onOpenChange={setCancelConfirmOpen}
        title="Cancel Invoice"
        description="Are you sure you want to cancel this invoice? This action cannot be undone."
        confirmText="Cancel Invoice"
        variant="destructive"
        onConfirm={() => {
          if (invoiceToCancel) cancelMutation.mutate(invoiceToCancel)
        }}
        loading={cancelMutation.isPending}
      />

      <ConfirmDialog
        open={markPaidConfirmOpen}
        onOpenChange={setMarkPaidConfirmOpen}
        title="Mark as Paid"
        description="This will record a payment for the full invoice amount and mark it as paid. A receipt will be sent to the client."
        confirmText="Mark as Paid"
        onConfirm={() => {
          if (invoiceToMarkPaid) markPaidMutation.mutate(invoiceToMarkPaid)
        }}
        loading={markPaidMutation.isPending}
      />
    </div>
  )
}

function CreateInvoiceModal({
  open,
  onClose,
  clients,
  onSubmit,
  loading,
}: {
  open: boolean
  onClose: () => void
  clients: Client[]
  onSubmit: (data: CreateInvoiceInput) => void
  loading: boolean
}) {
  const emptyItem = (): CreateInvoiceItemInput => ({
    description: '',
    quantity: 1,
    unit_price: 0,
  })

  const [clientId, setClientId] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [description, setDescription] = useState('')
  const [items, setItems] = useState<CreateInvoiceItemInput[]>([emptyItem()])

  const lineTotal = (item: CreateInvoiceItemInput) =>
    (Number(item.quantity) || 0) * (Number(item.unit_price) || 0)

  const runningTotal = items.reduce((sum, item) => sum + lineTotal(item), 0)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      client_id: clientId,
      due_date: dueDate,
      description: description || undefined,
      items: items.filter((i) => i.description.trim()),
    })
  }

  const isValid =
    clientId &&
    dueDate &&
    items.some((i) => i.description.trim() && lineTotal(i) > 0)

  return (
    <Modal open={open} onClose={onClose} title="Create Invoice">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Client</label>
          <Select
            options={clients.map((c) => ({ value: c.id, label: c.name }))}
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            placeholder="Select a client"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Line items</label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setItems([...items, emptyItem()])}
            >
              Add row
            </Button>
          </div>
          {items.map((item, index) => (
            <div key={index} className="grid grid-cols-12 gap-2 items-end">
              <div className="col-span-5">
                <Input
                  placeholder="Description"
                  value={item.description}
                  onChange={(e) => {
                    const next = [...items]
                    next[index] = { ...item, description: e.target.value }
                    setItems(next)
                  }}
                />
              </div>
              <div className="col-span-2">
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Qty"
                  className="font-mono"
                  value={item.quantity || ''}
                  onChange={(e) => {
                    const next = [...items]
                    next[index] = {
                      ...item,
                      quantity: parseFloat(e.target.value) || 0,
                    }
                    setItems(next)
                  }}
                />
              </div>
              <div className="col-span-2">
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Price"
                  className="font-mono"
                  value={item.unit_price || ''}
                  onChange={(e) => {
                    const next = [...items]
                    next[index] = {
                      ...item,
                      unit_price: parseFloat(e.target.value) || 0,
                    }
                    setItems(next)
                  }}
                />
              </div>
              <div className="col-span-2 text-right text-sm font-mono py-2">
                {formatCurrency(lineTotal(item))}
              </div>
              <div className="col-span-1">
                {items.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => setItems(items.filter((_, i) => i !== index))}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          ))}
          <div className="flex justify-end pt-1">
            <span className="text-sm text-muted-foreground mr-2">Total</span>
            <span className="font-bold font-mono">{formatCurrency(runningTotal)}</span>
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Due Date</label>
          <Input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Notes</label>
          <Input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional invoice notes"
          />
        </div>

        <div className="flex justify-end gap-2.5 pt-3">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading || !isValid}>
            {loading ? 'Creating...' : 'Create & Send'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function PaymentModal({
  open,
  onClose,
  invoice,
  onSubmit,
  loading,
}: {
  open: boolean
  onClose: () => void
  invoice: Invoice | null
  onSubmit: (data: CreatePaymentInput) => void
  loading: boolean
}) {
  const [formData, setFormData] = useState<CreatePaymentInput>({
    amount: 0,
    payment_method: 'bank_transfer',
    reference: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <Modal open={open} onClose={onClose} title="Record Payment">
      {invoice && (
        <div className="mb-4 p-3 rounded-lg bg-secondary border border-border">
          <p className="text-xs text-muted-foreground mb-0.5">Invoice Amount</p>
          <p className="text-lg font-bold font-mono tabular-nums">
            {formatCurrency(invoice.amount)}
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Payment Amount</label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={formData.amount || ''}
            onChange={(e) =>
              setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })
            }
            placeholder="0.00"
            className="font-mono"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Payment Method</label>
          <Select
            options={[
              { value: 'bank_transfer', label: 'Bank Transfer' },
              { value: 'credit_card', label: 'Credit Card' },
              { value: 'cash', label: 'Cash' },
              { value: 'check', label: 'Check' },
            ]}
            value={formData.payment_method}
            onChange={(e) =>
              setFormData({ ...formData, payment_method: e.target.value })
            }
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Reference</label>
          <Input
            value={formData.reference || ''}
            onChange={(e) =>
              setFormData({ ...formData, reference: e.target.value })
            }
            placeholder="Payment reference (optional)"
          />
        </div>

        <div className="flex justify-end gap-2.5 pt-3">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading || formData.amount <= 0}>
            {loading ? 'Processing...' : 'Record Payment'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function InvoiceDetailsDrawer({
  open,
  onClose,
  invoiceId,
  onResend,
}: {
  open: boolean
  onClose: () => void
  invoiceId: string | null
  onResend: (id: string) => void
}) {
  const { success } = useToast()

  const { data: invoice, isLoading } = useQuery({
    queryKey: ['invoice', invoiceId],
    queryFn: () => invoicesApi.get(invoiceId!),
    enabled: open && Boolean(invoiceId),
  })

  const { data: payments } = useQuery({
    queryKey: ['invoice-payments', invoiceId],
    queryFn: () => invoicesApi.getPayments(invoiceId!),
    enabled: open && Boolean(invoiceId),
  })

  if (!open || !invoiceId) return null

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Invoice Details"
      className="max-w-2xl"
    >
      {isLoading || !invoice ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">Invoice Number</p>
              <p className="text-base font-semibold font-mono">
                {invoice.invoice_number || `#${invoice.id.slice(0, 8)}`}
              </p>
              {invoice.client_name && (
                <p className="text-sm text-muted-foreground mt-1">
                  {invoice.client_name}
                </p>
              )}
            </div>
            <Badge variant={getStatusBadgeVariant(invoice.status)} className="text-xs">
              {invoice.status}
            </Badge>
          </div>

          {invoice.items && invoice.items.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="text-left py-2">Description</th>
                    <th className="text-right py-2">Qty</th>
                    <th className="text-right py-2">Unit</th>
                    <th className="text-right py-2">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.items.map((item, idx) => (
                    <tr key={item.id ?? idx} className="border-b border-border/50">
                      <td className="py-2">{item.description}</td>
                      <td className="py-2 text-right font-mono">{item.quantity}</td>
                      <td className="py-2 text-right font-mono">
                        {formatCurrency(item.unit_price)}
                      </td>
                      <td className="py-2 text-right font-mono">
                        {formatCurrency(item.line_total ?? 0)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 rounded-lg bg-secondary border border-border">
              <p className="text-xs text-muted-foreground mb-0.5">Amount</p>
              <p className="text-xl font-bold font-mono tabular-nums">
                {formatCurrency(invoice.amount)}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-secondary border border-border">
              <p className="text-xs text-muted-foreground mb-0.5">Due Date</p>
              <p className="text-lg font-semibold">
                {invoice.due_date
                  ? format(new Date(invoice.due_date), 'MMM d, yyyy')
                  : 'N/A'}
              </p>
            </div>
          </div>

          {invoice.description && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Notes</p>
              <p className="text-sm">{invoice.description}</p>
            </div>
          )}

          {payments && payments.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-2">Payments</p>
              <div className="space-y-2">
                {payments.map((payment: Payment) => (
                  <div
                    key={payment.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-border text-sm"
                  >
                    <div>
                      <p className="font-mono">{formatCurrency(payment.amount)}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(payment.payment_date), 'MMM d, yyyy')} ·{' '}
                        {payment.payment_method}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        invoicesApi
                          .downloadReceipt(invoice.id, payment.id)
                          .then((blob) => {
                            downloadBlob(blob, `receipt_${payment.id}.pdf`)
                          })
                      }}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2.5 pt-3 border-t border-border">
            <Button
              variant="outline"
              className="flex-1 min-w-[140px]"
              onClick={() => {
                invoicesApi.downloadPdf(invoice.id).then((blob) => {
                  downloadBlob(
                    blob,
                    `invoice_${invoice.invoice_number || invoice.id}.pdf`
                  )
                })
              }}
            >
              <Download className="h-4 w-4 mr-2" />
              Download PDF
            </Button>
            {invoice.share_token && (
              <Button
                variant="outline"
                className="flex-1 min-w-[140px]"
                onClick={() => {
                  const url = `${window.location.origin}/i/${invoice.share_token}`
                  navigator.clipboard.writeText(url)
                  success('Share link copied')
                }}
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy link
              </Button>
            )}
            {invoice.status === 'sent' && (
              <Button
                variant="outline"
                className="flex-1 min-w-[140px]"
                onClick={() => onResend(invoice.id)}
              >
                <Send className="h-4 w-4 mr-2" />
                Resend Email
              </Button>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}
