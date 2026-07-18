import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { Save, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Skeleton,
} from '@/components/ui'
import { useToast } from '@/hooks/useToast'
import { settingsApi } from '@/services/settings'
import type {
  BusinessSettings,
  BusinessSettingsInput,
} from '@/services/settings'

const currencies = [
  { value: 'USD', label: 'USD — US Dollar' },
  { value: 'EUR', label: 'EUR — Euro' },
  { value: 'GBP', label: 'GBP — British Pound' },
  { value: 'JPY', label: 'JPY — Japanese Yen' },
  { value: 'CAD', label: 'CAD — Canadian Dollar' },
  { value: 'AUD', label: 'AUD — Australian Dollar' },
]

export function SettingsPage() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToast()

  const {
    data: settings,
    isLoading,
    isError,
    error: queryError,
  } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
    retry: false,
  })

  const updateMutation = useMutation({
    mutationFn: settingsApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      success('Settings saved successfully')
    },
    onError: () => showError('Failed to save settings'),
  })

  const createMutation = useMutation({
    mutationFn: settingsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      success('Settings saved successfully')
    },
    onError: () => showError('Failed to save settings'),
  })

  const handleSubmit = (formData: BusinessSettingsInput) => {
    if (settings) {
      updateMutation.mutate(formData)
    } else {
      createMutation.mutate(formData)
    }
  }

  const isPending = updateMutation.isPending || createMutation.isPending
  const isFirstTime =
    isError && isAxiosError(queryError) && queryError.response?.status === 404
  const hasLoadError = isError && !isFirstTime

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Business Settings
        </h1>
        <p className="text-muted-foreground mt-1">
          Manage your business information for invoices and emails
        </p>
      </div>

      {isLoading ? (
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      ) : hasLoadError ? (
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-6 w-6 text-destructive" />
            <p className="mt-3 font-medium">Business settings could not be loaded</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Check your connection and try again.
            </p>
          </CardContent>
        </Card>
      ) : (
        <SettingsForm
          key={settings?.id ?? 'new-settings'}
          settings={settings}
          isFirstTime={isFirstTime}
          isPending={isPending}
          onSubmit={handleSubmit}
        />
      )}
    </div>
  )
}

function SettingsForm({
  settings,
  isFirstTime,
  isPending,
  onSubmit,
}: {
  settings?: BusinessSettings
  isFirstTime: boolean
  isPending: boolean
  onSubmit: (data: BusinessSettingsInput) => void
}) {
  const [formData, setFormData] = useState<BusinessSettingsInput>({
    business_name: settings?.business_name || '',
    business_email: settings?.business_email || '',
    phone: settings?.phone || '',
    address: settings?.address || '',
    currency: settings?.currency || 'USD',
    logo_url: settings?.logo_url || '',
  })

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    onSubmit(formData)
  }

  return (
        <form onSubmit={handleSubmit}>
          {isFirstTime && (
            <div className="mb-4 flex items-start gap-3 rounded-lg bg-primary/5 border border-primary/10 p-4">
              <AlertCircle className="h-5 w-5 text-primary mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium">Set up your business profile</p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  Configure your business details to include them in invoices and
                  emails.
                </p>
              </div>
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Business Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Business Name *</label>
                  <Input
                    value={formData.business_name}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        business_name: e.target.value,
                      })
                    }
                    placeholder="Your Business Name"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Business Email *</label>
                  <Input
                    type="email"
                    value={formData.business_email}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        business_email: e.target.value,
                      })
                    }
                    placeholder="billing@yourbusiness.com"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Phone</label>
                  <Input
                    value={formData.phone || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, phone: e.target.value })
                    }
                    placeholder="+1 234 567 8900"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Currency</label>
                  <Select
                    options={currencies}
                    value={formData.currency}
                    onChange={(e) =>
                      setFormData({ ...formData, currency: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-1.5 md:col-span-2">
                  <label className="text-sm font-medium">Address</label>
                  <textarea
                    className="flex min-h-[80px] w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm text-foreground ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 transition-colors"
                    value={formData.address || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, address: e.target.value })
                    }
                    placeholder="123 Business St, City, State 12345"
                  />
                </div>

                <div className="space-y-1.5 md:col-span-2">
                  <label className="text-sm font-medium">Logo URL</label>
                  <Input
                    value={formData.logo_url || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, logo_url: e.target.value })
                    }
                    placeholder="https://example.com/logo.png"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-3">
                <Button type="submit" disabled={isPending}>
                  {isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  {isPending ? 'Saving...' : 'Save Settings'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>
  )
}
