import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
  Tooltip,
  ClientSearchCombobox,
  ProductSearchCombobox,
} from '@/components/ui'
import { useToast } from '@/hooks/useToast'
import { useSettings } from '@/hooks/useSettings'
import { getErrorMessage } from '@/lib/axios'
import { formatCurrency } from '@/lib/utils'
import { downloadBlob, FILE_EXTENSIONS } from '@/lib/download'
import { invoiceItemsTotal, lineItemTotal } from '@/lib/invoice-items'
import { invoicesApi, clientsApi, productsApi } from '@/services'
import type { ExportFormat } from '@/lib/download'
import {
  Invoice,
  Client,
  CreateInvoiceInput,
  CreatePaymentInput,
  CreateInvoiceItemInput,
  Payment,
} from '@/types'

const PAGE_SIZE = 50

const statusOptions = [
  { value: 'all', label: 'All Status' },
  { value: 'draft', label: 'Draft' },
  { value: 'sent', label: 'Sent' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'paid', label: 'Paid' },
  { value: 'partial', label: 'Partial' },
  { value: 'cancelled', label: 'Cancelled' },
]


export function InvoicesPage() {
  const queryClient = useQueryClient()
  const { success, error } = useToast()
  const { currency } = useSettings()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(0)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createFormKey, setCreateFormKey] = useState(0)
  const [paymentModalOpen, setPaymentModalOpen] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)
  const [detailsInvoice, setDetailsInvoice] = useState<Invoice | null>(null)
  const [cancelConfirmOpen, setCancelConfirmOpen] = useState(false)
  const [invoiceToCancel, setInvoiceToCancel] = useState<string | null>(null)
  const [markPaidConfirmOpen, setMarkPaidConfirmOpen] = useState(false)
  const [invoiceToMarkPaid, setInvoiceToMarkPaid] = useState<string | null>(null)

  const { data: invoicePage, isLoading } = useQuery({
    queryKey: ['invoices', page, statusFilter],
    queryFn: () =>
      invoicesApi.list({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        status: statusFilter === 'all' ? undefined : statusFilter,
      }),
  })

  const invoices = invoicePage?.items
  const totalInvoices = invoicePage?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(totalInvoices / PAGE_SIZE))

  const { data: clientsPage } = useQuery({
    queryKey: ['clients', 'options'],
    queryFn: () => clientsApi.list({ limit: 200, offset: 0 }),
  })

  const clients = clientsPage?.items

  const createMutation = useMutation({
    mutationFn: (input: CreateInvoiceInput) => invoicesApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setCreateFormKey((key) => key + 1)
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

  const sendMutation = useMutation({
    mutationFn: (id: string) => invoicesApi.send(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      success('Invoice sent successfully')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const filteredInvoices = invoices?.filter((invoice) => {
    const matchesSearch =
      !search ||
      invoice.description?.toLowerCase().includes(search.toLowerCase()) ||
      invoice.invoice_number?.toLowerCase().includes(search.toLowerCase()) ||
      invoice.client_name?.toLowerCase().includes(search.toLowerCase())
    return matchesSearch
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
            Create, send, and track client invoices
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ExportDropdown onExport={handleExport} />
          <Button onClick={() => {
            setCreateFormKey((key) => key + 1)
            setCreateModalOpen(true)
          }}>
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
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setPage(0)
          }}
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
          {!search && statusFilter === 'all' && (
            <Button className="mt-4" onClick={() => {
              setCreateFormKey((key) => key + 1)
              setCreateModalOpen(true)
            }}>
              <Plus className="h-4 w-4 mr-2" />
              Create Invoice
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredInvoices?.map((invoice) => (
              <div key={invoice.id}>
                <Card className="hover:border-primary/30 transition-colors group">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <Badge variant={getStatusBadgeVariant(invoice.status)}>
                        {invoice.status}
                      </Badge>
                      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Tooltip label="View invoice details">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={() => setDetailsInvoice(invoice)}
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </Button>
                        </Tooltip>
                        {invoice.status === 'draft' && (
                          <Tooltip label="Send invoice">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => sendMutation.mutate(invoice.id)}
                            >
                              <Send className="h-3.5 w-3.5" />
                            </Button>
                          </Tooltip>
                        )}
                        {invoice.status !== 'paid' &&
                          invoice.status !== 'cancelled' && (
                            <>
                              <Tooltip label="Record payment">
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
                              </Tooltip>
                              {(invoice.status === 'sent' ||
                                invoice.status === 'overdue') && (
                                <Tooltip label="Mark as paid">
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
                                </Tooltip>
                              )}
                              {invoice.status !== 'overdue' &&
                                invoice.status !== 'partial' && (
                                  <Tooltip label="Cancel invoice">
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
                                  </Tooltip>
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
                        {formatCurrency(invoice.amount, currency)}
                      </span>
                      <span className="text-xs font-mono text-muted-foreground">
                        {invoice.invoice_number || `#${invoice.id.slice(0, 8)}`}
                      </span>
                    </div>

                    {(invoice.status === 'partial' ||
                      Number(invoice.paid_amount ?? 0) > 0) && (
                      <div className="mb-2 space-y-1">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>
                            Paid {formatCurrency(invoice.paid_amount ?? 0, currency)}
                          </span>
                          <span>
                            Due {formatCurrency(invoice.balance_due ?? invoice.amount, currency)}
                          </span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
                          <div
                            className="h-full rounded-full bg-primary transition-all"
                            style={{
                              width: `${Math.min(
                                100,
                                (Number(invoice.paid_amount ?? 0) /
                                  Math.max(Number(invoice.amount), 1)) *
                                  100
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}

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
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-muted-foreground">
                Page {page + 1} of {totalPages} · {totalInvoices} invoices
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page + 1 >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      <CreateInvoiceModal
        open={createModalOpen}
        formKey={createFormKey}
        onClose={() => setCreateModalOpen(false)}
        clients={clients || []}
        currency={currency}
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
        currency={currency}
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
        currency={currency}
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
  formKey,
  onClose,
  clients,
  currency,
  onSubmit,
  loading,
}: {
  open: boolean
  formKey: number
  onClose: () => void
  clients: Client[]
  currency: string
  onSubmit: (data: CreateInvoiceInput) => void
  loading: boolean
}) {
  if (!open) return null

  return (
    <Modal open={open} onClose={onClose} title="Create Invoice">
      <CreateInvoiceForm
        key={formKey}
        clients={clients}
        currency={currency}
        onSubmit={onSubmit}
        loading={loading}
        onCancel={onClose}
      />
    </Modal>
  )
}

function CreateInvoiceForm({
  clients,
  currency,
  onSubmit,
  loading,
  onCancel,
}: {
  clients: Client[]
  currency: string
  onSubmit: (data: CreateInvoiceInput) => void
  loading: boolean
  onCancel: () => void
}) {
  const emptyItem = (): CreateInvoiceItemInput => ({
    description: '',
    quantity: 1,
    unit_price: 0,
  })

  const { data: productsPage } = useQuery({
    queryKey: ['products', 'options'],
    queryFn: () => productsApi.list({ limit: 200 }),
  })
  const productOptions = productsPage?.items ?? []

  const [clientId, setClientId] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [description, setDescription] = useState('')
  const [items, setItems] = useState<CreateInvoiceItemInput[]>([emptyItem()])

  const lineTotal = (item: CreateInvoiceItemInput) =>
    lineItemTotal({ quantity: Number(item.quantity), unit_price: Number(item.unit_price) })

  const runningTotal = invoiceItemsTotal(
    items.map((item) => ({
      quantity: Number(item.quantity) || 0,
      unit_price: Number(item.unit_price) || 0,
    }))
  )

  const submitInvoice = (sendNow: boolean) => {
    onSubmit({
      client_id: clientId,
      due_date: dueDate,
      description: description || undefined,
      items: items
        .filter(
          (i) =>
            (i.description.trim() || i.product_id) &&
            lineTotal(i) > 0
        )
        .map((i) => ({
          description: i.description,
          quantity: Number(i.quantity),
          unit_price: Number(i.unit_price),
          product_id: i.product_id,
        })),
      send_now: sendNow,
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    submitInvoice(true)
  }

  const isValid =
    clientId &&
    dueDate &&
    items.some(
      (i) => (i.description.trim() || i.product_id) && lineTotal(i) > 0
    )

  return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Client</label>
          <ClientSearchCombobox
            value={clientId}
            onChange={setClientId}
            initialClients={clients}
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
              <div className="col-span-5 space-y-1.5">
                <ProductSearchCombobox
                  value={item.product_id}
                  initialProducts={productOptions}
                  onSelect={(product) => {
                    const next = [...items]
                    next[index] = {
                      ...item,
                      product_id: product.id,
                      description: product.name,
                      unit_price: Number(product.unit_price),
                    }
                    setItems(next)
                  }}
                />
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
                {formatCurrency(lineTotal(item), currency)}
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
            <span className="font-bold font-mono">{formatCurrency(runningTotal, currency)}</span>
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
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={loading || !isValid}
            onClick={() => submitInvoice(false)}
          >
            {loading ? 'Saving...' : 'Save as draft'}
          </Button>
          <Button type="submit" disabled={loading || !isValid}>
            {loading ? 'Creating...' : 'Create & Send'}
          </Button>
        </div>
      </form>
  )
}

function PaymentModal({
  open,
  onClose,
  invoice,
  currency,
  onSubmit,
  loading,
}: {
  open: boolean
  onClose: () => void
  invoice: Invoice | null
  currency: string
  onSubmit: (data: CreatePaymentInput) => void
  loading: boolean
}) {
  if (!open || !invoice) return null

  return (
    <Modal open={open} onClose={onClose} title="Record Payment">
      <PaymentForm
        key={invoice.id}
        invoice={invoice}
        currency={currency}
        onSubmit={onSubmit}
        loading={loading}
        onCancel={onClose}
      />
    </Modal>
  )
}

function PaymentForm({
  invoice,
  currency,
  onSubmit,
  loading,
  onCancel,
}: {
  invoice: Invoice
  currency: string
  onSubmit: (data: CreatePaymentInput) => void
  loading: boolean
  onCancel: () => void
}) {
  const invoiceTotal = Number(invoice.amount)
  const paidSoFar = Number(invoice.paid_amount ?? 0)
  const balanceDue = Number(invoice.balance_due ?? invoiceTotal - paidSoFar)
  const [formData, setFormData] = useState<CreatePaymentInput>({
    amount: balanceDue > 0 ? balanceDue : 0,
    payment_method: 'bank_transfer',
    reference: '',
  })

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    onSubmit(formData)
  }

  return (
    <>
      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-secondary p-3">
          <p className="mb-0.5 text-xs text-muted-foreground">Total</p>
          <p className="font-mono text-lg font-bold tabular-nums">
            {formatCurrency(invoice.amount, currency)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-secondary p-3">
          <p className="mb-0.5 text-xs text-muted-foreground">Paid</p>
          <p className="font-mono text-lg font-bold tabular-nums">
            {formatCurrency(paidSoFar, currency)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-secondary p-3">
          <p className="mb-0.5 text-xs text-muted-foreground">Balance</p>
          <p className="font-mono text-lg font-bold tabular-nums">
            {formatCurrency(balanceDue, currency)}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Payment Amount</label>
            {balanceDue > 0 && (
              <Button
                type="button"
                variant="link"
                className="h-auto px-0 text-xs"
                onClick={() => setFormData((current) => ({ ...current, amount: balanceDue }))}
              >
                Pay remaining
              </Button>
            )}
          </div>
          <Input
            type="number"
            step="0.01"
            min="0"
            max={balanceDue}
            value={formData.amount || ''}
            onChange={(event) =>
              setFormData({
                ...formData,
                amount: Math.min(parseFloat(event.target.value) || 0, balanceDue),
              })
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
            onChange={(event) =>
              setFormData({ ...formData, payment_method: event.target.value })
            }
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Reference</label>
          <Input
            value={formData.reference || ''}
            onChange={(event) =>
              setFormData({ ...formData, reference: event.target.value })
            }
            placeholder="Payment reference (optional)"
          />
        </div>

        <div className="flex justify-end gap-2.5 pt-3">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading || formData.amount <= 0}>
            {loading ? 'Processing...' : 'Record Payment'}
          </Button>
        </div>
      </form>
    </>
  )
}

function InvoiceDetailsDrawer({
  open,
  onClose,
  invoiceId,
  currency,
  onResend,
}: {
  open: boolean
  onClose: () => void
  invoiceId: string | null
  currency: string
  onResend: (id: string) => void
}) {
  const { success, error: showError } = useToast()

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

  const downloadPdfMutation = useMutation({
    mutationFn: (id: string) => invoicesApi.downloadPdf(id),
    onSuccess: (blob) => {
      if (!invoice) return
      downloadBlob(blob, `invoice_${invoice.invoice_number || invoice.id}.pdf`)
      success('Invoice PDF downloaded')
    },
    onError: (err: unknown) => showError(getErrorMessage(err)),
  })

  const downloadReceiptMutation = useMutation({
    mutationFn: ({ invoiceId, paymentId }: { invoiceId: string; paymentId: string }) =>
      invoicesApi.downloadReceipt(invoiceId, paymentId),
    onSuccess: (blob, variables) => {
      downloadBlob(blob, `receipt_${variables.paymentId}.pdf`)
      success('Receipt downloaded')
    },
    onError: (err: unknown) => showError(getErrorMessage(err)),
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
        <div className="invoice-document rounded-xl p-6 md:p-8 space-y-5">
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
                        {formatCurrency(item.unit_price, currency)}
                      </td>
                      <td className="py-2 text-right font-mono">
                        {formatCurrency(item.line_total ?? 0, currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-lg border border-border bg-secondary p-4">
              <p className="mb-0.5 text-xs text-muted-foreground">Total</p>
              <p className="font-mono text-xl font-bold tabular-nums">
                {formatCurrency(invoice.amount, currency)}
              </p>
            </div>
            <div className="rounded-lg border border-border bg-secondary p-4">
              <p className="mb-0.5 text-xs text-muted-foreground">Paid</p>
              <p className="font-mono text-xl font-bold tabular-nums">
                {formatCurrency(invoice.paid_amount ?? 0, currency)}
              </p>
            </div>
            <div className="rounded-lg border border-border bg-secondary p-4">
              <p className="mb-0.5 text-xs text-muted-foreground">Balance</p>
              <p className="font-mono text-xl font-bold tabular-nums">
                {formatCurrency(invoice.balance_due ?? invoice.amount, currency)}
              </p>
            </div>
            <div className="rounded-lg border border-border bg-secondary p-4">
              <p className="mb-0.5 text-xs text-muted-foreground">Due Date</p>
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
                      <p className="font-mono">{formatCurrency(payment.amount, currency)}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(payment.payment_date), 'MMM d, yyyy')} ·{' '}
                        {payment.payment_method}
                      </p>
                    </div>
                    <Tooltip label="Download receipt PDF">
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={downloadReceiptMutation.isPending}
                        onClick={() =>
                          downloadReceiptMutation.mutate({
                            invoiceId: invoice.id,
                            paymentId: payment.id,
                          })
                        }
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </Tooltip>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2.5 pt-3 border-t border-border">
            <Button
              variant="outline"
              className="min-w-[140px] flex-1"
              disabled={downloadPdfMutation.isPending}
              onClick={() => downloadPdfMutation.mutate(invoice.id)}
            >
              <Download className="mr-2 h-4 w-4" />
              {downloadPdfMutation.isPending ? 'Downloading…' : 'Download PDF'}
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
