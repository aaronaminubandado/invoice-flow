import { useEffect, useId, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { productsApi } from '@/services/products'
import type { Product } from '@/types'

function filterProducts(products: Product[], query: string): Product[] {
  const normalized = query.trim().toLowerCase()
  if (!normalized) {
    return products
  }

  return products.filter(
    (product) =>
      product.name.toLowerCase().includes(normalized) ||
      (product.sku ?? '').toLowerCase().includes(normalized) ||
      (product.description ?? '').toLowerCase().includes(normalized)
  )
}

interface ProductSearchComboboxProps {
  value?: string
  onSelect: (product: Product) => void
  initialProducts?: Product[]
  placeholder?: string
  resetOnSelect?: boolean
}

export function ProductSearchCombobox({
  value,
  onSelect,
  initialProducts = [],
  placeholder = 'Search products…',
  resetOnSelect = false,
}: ProductSearchComboboxProps) {
  const listboxId = useId()
  const containerRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  const selectedProduct =
    initialProducts.find((product) => product.id === value)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250)
    return () => window.clearTimeout(timer)
  }, [query])

  const { data: searchResults = [], isFetching } = useQuery({
    queryKey: ['products', 'search', debouncedQuery],
    queryFn: () => productsApi.search(debouncedQuery),
    enabled: open,
    staleTime: 1000 * 60,
  })

  const localMatches = filterProducts(initialProducts, debouncedQuery)
  const results = debouncedQuery
    ? searchResults.length > 0
      ? searchResults
      : localMatches
    : initialProducts.length > 0
      ? initialProducts
      : searchResults

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const displayValue = open
    ? query
    : resetOnSelect || !value
      ? ''
      : selectedProduct?.name ?? ''

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={listboxId}
          aria-autocomplete="list"
          value={displayValue}
          placeholder={placeholder}
          onFocus={() => {
            setOpen(true)
            setQuery(selectedProduct?.name ?? '')
          }}
          onChange={(event) => {
            setQuery(event.target.value)
            setOpen(true)
          }}
          className="flex h-9 w-full rounded-lg border border-input bg-background px-8 py-1.5 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
      </div>

      {open && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute z-50 mt-1 max-h-48 w-full overflow-auto rounded-lg border border-border bg-popover p-1 shadow-lg"
        >
          {isFetching && debouncedQuery && searchResults.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">Searching…</li>
          ) : results.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">No products found</li>
          ) : (
            results.map((product) => (
              <li key={product.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={product.id === value}
                  onClick={() => {
                    onSelect(product)
                    if (resetOnSelect) {
                      setQuery('')
                    } else {
                      setQuery(product.name)
                    }
                    setOpen(false)
                  }}
                  className={cn(
                    'flex w-full flex-col rounded-md px-3 py-2 text-left text-sm hover:bg-accent',
                    product.id === value && 'bg-accent'
                  )}
                >
                  <span className="font-medium">{product.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {product.sku ? `${product.sku} · ` : ''}
                    ${Number(product.unit_price).toFixed(2)}
                  </span>
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}
