import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Download, FileText } from 'lucide-react'
import { format } from 'date-fns'
import { Button, Badge, getStatusBadgeVariant } from '@/components/ui'
import { publicInvoicesApi } from '@/services/public'
import { formatCurrency } from '@/lib/utils'

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
      <div className="min-h-screen flex items-center justify-center bg-background">
        <span className="text-muted-foreground">Loading invoice...</span>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background p-6 text-center">
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
    <div className="min-h-screen bg-secondary/30 py-10 px-4">
      <div className="max-w-3xl mx-auto bg-card border border-border rounded-xl shadow-sm p-8 md:p-10">
        {data.business && (
          <div className="mb-8 pb-6 border-b border-border">
            <h1 className="text-xl font-semibold">{data.business.business_name}</h1>
            <p className="text-sm text-muted-foreground">{data.business.business_email}</p>
            {data.business.phone && (
              <p className="text-sm text-muted-foreground">{data.business.phone}</p>
            )}
            {data.business.address && (
              <p className="text-sm text-muted-foreground whitespace-pre-line">
                {data.business.address}
              </p>
            )}
          </div>
        )}

        <div className="flex items-start justify-between gap-4 mb-8">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Invoice</p>
            <p className="text-2xl font-semibold font-mono">
              {data.invoice_number ?? '—'}
            </p>
            <p className="text-sm text-muted-foreground mt-1">Bill to: {data.client_name}</p>
          </div>
          <Badge variant={getStatusBadgeVariant(data.status)}>{data.status}</Badge>
        </div>

        {data.items.length > 0 ? (
          <div className="overflow-x-auto mb-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="text-left py-2 font-medium">Description</th>
                  <th className="text-right py-2 font-medium">Qty</th>
                  <th className="text-right py-2 font-medium">Unit</th>
                  <th className="text-right py-2 font-medium">Total</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="border-b border-border/60">
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
          <p className="text-sm mb-6">{data.description}</p>
        ) : null}

        <div className="grid sm:grid-cols-2 gap-4 mb-8">
          <div>
            <p className="text-xs text-muted-foreground">Due date</p>
            <p className="font-medium">
              {data.due_date ? format(new Date(data.due_date), 'MMM d, yyyy') : '—'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="text-2xl font-bold font-mono">
              {formatCurrency(data.amount, currency)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Paid</p>
            <p className="font-mono">{formatCurrency(data.paid_amount, currency)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Balance due</p>
            <p className="font-mono font-semibold">
              {formatCurrency(data.balance_due, currency)}
            </p>
          </div>
        </div>

        <Button
          className="w-full sm:w-auto"
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
