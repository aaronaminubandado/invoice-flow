import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileText, Mail, Lock, ArrowRight } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { supabase } from '@/lib/supabase'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const demoEmail = import.meta.env.VITE_DEMO_EMAIL as string | undefined
  const demoPassword = import.meta.env.VITE_DEMO_PASSWORD as string | undefined

  const signIn = async (creds: { email: string; password: string }) => {
    const { data, error: authError } = await supabase.auth.signInWithPassword(creds)

    if (authError) throw authError

    if (data.session) {
      navigate('/dashboard')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await signIn({ email, password })
    } catch (err: any) {
      setError(err.message || 'Failed to sign in')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoSignIn = async () => {
    if (!demoEmail || !demoPassword) {
      setError('Demo account is not configured.')
      return
    }

    setLoading(true)
    setError('')

    try {
      await signIn({ email: demoEmail, password: demoPassword })
    } catch (err: any) {
      setError(err.message || 'Failed to sign in to demo account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-background to-background" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative w-full max-w-[400px]"
      >
        <div className="glass-card rounded-2xl p-8">
          <div className="flex items-center justify-center gap-2.5 mb-8">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 border border-primary/50">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <span className="text-xl font-semibold tracking-tight">
              InvoiceFlow
            </span>
          </div>

          <h1 className="text-xl font-semibold text-center mb-1">
            Welcome back
          </h1>
          <p className="text-sm text-muted-foreground text-center mb-8">
            Sign in to your account to continue
          </p>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm"
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Signing in...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Sign in
                  <ArrowRight className="h-4 w-4" />
                </span>
              )}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="text-primary hover:underline font-medium">
              Sign up
            </Link>
          </p>

          <div className="mt-6 space-y-3 text-center text-xs text-muted-foreground">
            <Button
              type="button"
              variant="outline"
              className="w-full text-[13px]"
              onClick={handleDemoSignIn}
              disabled={loading}
            >
              Use shared demo account
            </Button>
            <div className="space-y-1.5">
              <p className="font-medium text-[11px] uppercase tracking-[0.16em] text-muted-foreground/80">
                Public demo environment
              </p>
              <p>
                Anyone can explore the app using the shared demo account.
                Data may be reset periodically, so please don&apos;t store any
                real or sensitive information.
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
