import { useEffect, useId, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { clientsApi } from '@/services/clients'
import type { Client } from '@/types'

function filterClients(clients: Client[], query: string): Client[] {
  const normalized = query.trim().toLowerCase()
  if (!normalized) {
    return clients
  }

  return clients.filter(
    (client) =>
      client.name.toLowerCase().includes(normalized) ||
      client.email.toLowerCase().includes(normalized)
  )
}

interface ClientSearchComboboxProps {
  value: string
  onChange: (clientId: string) => void
  initialClients?: Client[]
  placeholder?: string
}

export function ClientSearchCombobox({
  value,
  onChange,
  initialClients = [],
  placeholder = 'Search clients by name or email',
}: ClientSearchComboboxProps) {
  const listboxId = useId()
  const containerRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  const selectedClient =
    initialClients.find((client) => client.id === value)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250)
    return () => window.clearTimeout(timer)
  }, [query])

  const { data: searchResults = [], isFetching } = useQuery({
    queryKey: ['clients', 'search', debouncedQuery],
    queryFn: () => clientsApi.search(debouncedQuery),
    enabled: open && debouncedQuery.length > 0,
    staleTime: 1000 * 60,
  })

  const localMatches = filterClients(initialClients, debouncedQuery)
  const results = debouncedQuery
    ? searchResults.length > 0
      ? searchResults
      : localMatches
    : initialClients

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const displayValue = open ? query : selectedClient?.name ?? ''

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
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
            setQuery(selectedClient?.name ?? '')
          }}
          onChange={(event) => {
            setQuery(event.target.value)
            setOpen(true)
          }}
          className="flex h-10 w-full rounded-lg border border-input bg-background px-10 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      </div>

      {open && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-lg border border-border bg-popover p-1 shadow-lg"
        >
          {isFetching && debouncedQuery && searchResults.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">Searching…</li>
          ) : results.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">No clients found</li>
          ) : (
            results.map((client) => (
              <li key={client.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={client.id === value}
                  onClick={() => {
                    onChange(client.id)
                    setQuery(client.name)
                    setOpen(false)
                  }}
                  className={cn(
                    'flex w-full flex-col rounded-md px-3 py-2 text-left text-sm hover:bg-accent',
                    client.id === value && 'bg-accent'
                  )}
                >
                  <span className="font-medium">{client.name}</span>
                  <span className="text-xs text-muted-foreground">{client.email}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}
