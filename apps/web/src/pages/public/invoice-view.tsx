import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Download, FileText } from 'lucide-react'
import { format } from 'date-fns'
import { Button, Badge, getStatusBadgeVariant } from '@/components/ui'
import { publicInvoicesApi } from '@/services/public'
import { formatCurrency } from '@/lib/utils'
import { downloadBlob } from '@/lib/download'

export function PublicInvoicePage() {
  const { token } = useParams<{ token: string }>()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['public-invoice', token],
    queryFn: () => publicInvoicesApi.get(token!),
    enabled: Boolean(token),
    retry: false,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary/30">
        <span className="text-muted-foreground">Loading invoice...</span>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-secondary/30 p-6 text-center">
        <FileText className="h-12 w-12 text-muted-foreground mb-4" />
        <h1 className="text-lg font-semibold">Invoice not found</h1>
        <p className="text-sm text-muted-foreground mt-2 max-w-md">
          This invoice link is invalid or has been removed.
        </p>
      </div>
    )
  }

  const currency = data.business?.currency ?? 'USD'

  return (
    <div className="min-h-screen bg-secondary/40 py-8 px-4 sm:py-12">
      <div className="max-w-3xl mx-auto invoice-document rounded-lg p-8 md:p-12">
        {data.business && (
          <header className="mb-10 pb-6 border-b border-[var(--color-document-border)]">
            <p className="text-xs uppercase tracking-[0.2em] invoice-document-muted mb-2">
              From
            </p>
            <h1 className="text-2xl font-semibold tracking-tight">
              {data.business.business_name}
            </h1>
            <p className="text-sm invoice-document-muted mt-1">
              {data.business.business_email}
            </p>
            {data.business.phone && (
              <p className="text-sm invoice-document-muted">{data.business.phone}</p>
            )}
            {data.business.address && (
              <p className="text-sm invoice-document-muted whitespace-pre-line mt-1">
                {data.business.address}
              </p>
            )}
          </header>
        )}

        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] invoice-document-muted">
              Invoice
            </p>
            <p className="text-3xl font-semibold font-mono mt-1">
              {data.invoice_number ?? '—'}
            </p>
          </div>
          <Badge variant={getStatusBadgeVariant(data.status)}>{data.status}</Badge>
        </div>

        <section className="mb-8 pb-6 border-b border-[var(--color-document-border)]">
          <p className="text-xs uppercase tracking-[0.2em] invoice-document-muted mb-1">
            Bill to
          </p>
          <p className="text-lg font-medium">{data.client_name}</p>
          {data.due_date && (
            <p className="text-sm invoice-document-muted mt-2">
              Due {format(new Date(data.due_date), 'MMMM d, yyyy')}
            </p>
          )}
        </section>

        {data.items.length > 0 ? (
          <div className="overflow-x-auto mb-8">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-document-border)] invoice-document-muted">
                  <th className="text-left py-2 font-medium">Description</th>
                  <th className="text-right py-2 font-medium">Qty</th>
                  <th className="text-right py-2 font-medium">Unit</th>
                  <th className="text-right py-2 font-medium">Total</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="border-b border-[var(--color-document-border)]/70">
                    <td className="py-3">{item.description}</td>
                    <td className="py-3 text-right font-mono">{item.quantity}</td>
                    <td className="py-3 text-right font-mono">
                      {formatCurrency(item.unit_price, currency)}
                    </td>
                    <td className="py-3 text-right font-mono">
                      {formatCurrency(item.line_total, currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : data.description ? (
          <p className="text-sm mb-8">{data.description}</p>
        ) : null}

        <section className="grid sm:grid-cols-3 gap-4 mb-8 pt-4 border-t border-[var(--color-document-border)]">
          <div>
            <p className="text-xs invoice-document-muted">Total</p>
            <p className="text-2xl font-bold font-mono">
              {formatCurrency(data.amount, currency)}
            </p>
          </div>
          <div>
            <p className="text-xs invoice-document-muted">Paid</p>
            <p className="font-mono text-lg">{formatCurrency(data.paid_amount, currency)}</p>
          </div>
          <div>
            <p className="text-xs invoice-document-muted">Balance due</p>
            <p className="font-mono text-lg font-semibold">
              {formatCurrency(data.balance_due, currency)}
            </p>
          </div>
        </section>

        <Button
          variant="outline"
          className="border-[var(--color-document-border)]"
          onClick={() => {
            publicInvoicesApi.downloadPdf(token!).then((blob) => {
              downloadBlob(blob, `invoice_${data.invoice_number ?? token}.pdf`)
            })
          }}
        >
          <Download className="h-4 w-4 mr-2" />
          Download PDF
        </Button>
      </div>
    </div>
  )
}
