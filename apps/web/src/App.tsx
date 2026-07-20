import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MainLayout } from '@/components/layout'
import { ToastProvider } from '@/components/ui/toast'
import { ThemeProvider } from '@/contexts/theme'
import { useSession } from '@/hooks/useSession'
import { LoginPage } from '@/pages/auth/login'
import { RegisterPage } from '@/pages/auth/register'
import { ForgotPasswordPage } from '@/pages/auth/forgot-password'
import { ResetPasswordPage } from '@/pages/auth/reset-password'
import { PublicInvoicePage } from '@/pages/public/invoice-view'

const LandingPage = lazy(() =>
  import('@/pages/landing/landing-page').then((module) => ({
    default: module.LandingPage,
  }))
)
const DashboardPage = lazy(() =>
  import('@/pages/dashboard/dashboard').then((module) => ({
    default: module.DashboardPage,
  }))
)
const InvoicesPage = lazy(() =>
  import('@/pages/invoices/invoices').then((module) => ({
    default: module.InvoicesPage,
  }))
)
const ClientsPage = lazy(() =>
  import('@/pages/clients/clients').then((module) => ({
    default: module.ClientsPage,
  }))
)
const MetricsPage = lazy(() =>
  import('@/pages/metrics/metrics').then((module) => ({
    default: module.MetricsPage,
  }))
)
const SettingsPage = lazy(() =>
  import('@/pages/settings/settings').then((module) => ({
    default: module.SettingsPage,
  }))
)
const ProductsPage = lazy(() =>
  import('@/pages/products/products').then((module) => ({
    default: module.ProductsPage,
  }))
)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 30,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useSession()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <span className="text-muted-foreground text-sm">Loading...</span>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useSession()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <span className="text-muted-foreground text-sm">Loading...</span>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

function RouteFallback() {
  return (
    <div className="min-h-[40vh] flex items-center justify-center">
      <span className="text-muted-foreground text-sm">Loading...</span>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Routes>
              <Route path="/i/:token" element={<PublicInvoicePage />} />
              <Route
                path="/login"
                element={
                  <PublicRoute>
                    <LoginPage />
                  </PublicRoute>
                }
              />
              <Route
                path="/register"
                element={
                  <PublicRoute>
                    <RegisterPage />
                  </PublicRoute>
                }
              />
              <Route
                path="/forgot-password"
                element={
                  <PublicRoute>
                    <ForgotPasswordPage />
                  </PublicRoute>
                }
              />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route
                element={
                  <ProtectedRoute>
                    <MainLayout />
                  </ProtectedRoute>
                }
              >
                <Route
                  path="/dashboard"
                  element={
                    <Suspense fallback={<RouteFallback />}>
                      <DashboardPage />
                    </Suspense>
                  }
                />
                <Route
                  path="/invoices"
                  element={
                    <Suspense fallback={<RouteFallback />}>
                      <InvoicesPage />
                    </Suspense>
                  }
                />
                <Route
                  path="/clients"
                  element={
                    <Suspense fallback={<RouteFallback />}>
                      <ClientsPage />
                    </Suspense>
                  }
                />
                <Route
                  path="/products"
                  element={
                    <Suspense fallback={<RouteFallback />}>
                      <ProductsPage />
                    </Suspense>
                  }
                />
                <Route
                  path="/metrics"
                  element={
                    <Suspense fallback={<RouteFallback />}>
                      <MetricsPage />
                    </Suspense>
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <Suspense fallback={<RouteFallback />}>
                      <SettingsPage />
                    </Suspense>
                  }
                />
              </Route>

              <Route
                path="/"
                element={
                  <Suspense fallback={<RouteFallback />}>
                    <LandingPage />
                  </Suspense>
                }
              />

              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </QueryClientProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}

export default App
