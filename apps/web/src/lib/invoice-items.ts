export interface InvoiceLineItemInput {
  quantity: number
  unit_price: number
}

export function lineItemTotal(item: InvoiceLineItemInput): number {
  return (Number(item.quantity) || 0) * (Number(item.unit_price) || 0)
}

export function invoiceItemsTotal(items: InvoiceLineItemInput[]): number {
  return items.reduce((sum, item) => sum + lineItemTotal(item), 0)
}
