import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Lock } from 'lucide-react'
import { Button, PasswordInput } from '@/components/ui'
import { LogoMark } from '@/components/brand/logo-mark'
import { supabase } from '@/lib/supabase'

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    let active = true

    const prepareRecoverySession = async () => {
      const hash = window.location.hash.startsWith('#')
        ? window.location.hash.slice(1)
        : window.location.hash
      const params = new URLSearchParams(hash)
      const accessToken = params.get('access_token')
      const refreshToken = params.get('refresh_token')
      const type = params.get('type')

      if (accessToken && refreshToken && type === 'recovery') {
        const { error: sessionError } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        })
        if (!active) return
        if (sessionError) {
          setError(sessionError.message)
          return
        }
        window.history.replaceState({}, document.title, window.location.pathname)
      }

      const { data } = await supabase.auth.getSession()
      if (!active) return
      setReady(Boolean(data.session))
      if (!data.session) {
        setError('This reset link is invalid or has expired.')
      }
    }

    void prepareRecoverySession()

    return () => {
      active = false
    }
  }, [])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    const { error: updateError } = await supabase.auth.updateUser({ password })

    setLoading(false)

    if (updateError) {
      setError(updateError.message)
      return
    }

    setSuccess(true)
    await supabase.auth.signOut()
    window.setTimeout(() => navigate('/login'), 1500)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="relative w-full max-w-[400px] animate-fade-in">
        <div className="glass-card rounded-2xl p-8">
          <div className="mb-8 flex items-center justify-center gap-2.5">
            <LogoMark className="h-10 w-10" />
            <span className="text-xl font-semibold tracking-tight">InvoiceFlow</span>
          </div>

          <h1 className="text-center text-xl font-semibold">Choose a new password</h1>
          <p className="mb-8 mt-1 text-center text-sm text-muted-foreground">
            Enter and confirm your new password to finish resetting your account.
          </p>

          {error && (
            <div className="mb-4 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {success ? (
            <div className="space-y-5">
              <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 text-sm">
                Password updated. Redirecting you to sign in…
              </div>
            </div>
          ) : ready ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">New password</label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <PasswordInput
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="pl-10"
                    placeholder="At least 8 characters"
                    required
                    minLength={8}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium">Confirm password</label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <PasswordInput
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    className="pl-10"
                    placeholder="Repeat your password"
                    required
                    minLength={8}
                  />
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Updating…' : 'Update password'}
              </Button>
            </form>
          ) : (
            <p className="text-center text-sm text-muted-foreground">Verifying reset link…</p>
          )}

          <Link
            to="/login"
            className="mt-6 flex items-center justify-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  )
}
