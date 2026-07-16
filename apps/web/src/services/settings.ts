import { api } from '@/lib/axios'

export interface BusinessSettings {
  id: string
  user_id: string
  business_name: string
  business_email: string
  phone?: string
  address?: string
  currency: string
  logo_url?: string
  created_at: string
  updated_at: string
}

export interface BusinessSettingsInput {
  business_name: string
  business_email: string
  phone?: string
  address?: string
  currency?: string
  logo_url?: string
}

export const settingsApi = {
  get: async () => {
    const { data } = await api.get<BusinessSettings>('/settings')
    return data
  },

  create: async (input: BusinessSettingsInput) => {
    const { data } = await api.post<BusinessSettings>('/settings', input)
    return data
  },

  update: async (input: Partial<BusinessSettingsInput>) => {
    const { data } = await api.put<BusinessSettings>('/settings', input)
    return data
  },
}
