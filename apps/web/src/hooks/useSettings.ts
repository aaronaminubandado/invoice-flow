import { useQuery } from '@tanstack/react-query'
import { settingsApi } from '@/services/settings'

export function useSettings() {
  const query = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
    retry: false,
  })

  return {
    ...query,
    currency: query.data?.currency ?? 'USD',
    hasSettings: Boolean(query.data),
  }
}
