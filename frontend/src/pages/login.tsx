import { useState } from 'react'
import { useAuthStore } from '@/store/auth'
import { usePositionStore } from '@/store/positions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/toast'
import { Briefcase, Eye, EyeOff, Loader2 } from 'lucide-react'

interface LoginPageProps {
  onNavigateToRegister: () => void
  onLoginSuccess: () => void
}

export function LoginPage({ onNavigateToRegister, onLoginSuccess }: LoginPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password) return
    setLoading(true)
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '登录失败')
      }
      const data = await res.json()
      setAuth(data.access_token, data.user)
      toast.success('登录成功')
      onLoginSuccess()
    } catch (e: any) {
      toast.error(e.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo */}
        <div className="text-center">
          <span className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-primary text-primary-foreground mb-4">
            <Briefcase className="w-6 h-6" />
          </span>
          <h1 className="text-xl font-semibold">SmartTracker</h1>
          <p className="text-sm text-muted-foreground mt-1">智能求职管理</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">邮箱</label>
            <Input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">密码</label>
            <div className="relative">
              <Input
                type={showPwd ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <Button type="submit" className="w-full h-10" disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            {loading ? '登录中...' : '登录'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          还没有账号？{' '}
          <button
            onClick={onNavigateToRegister}
            className="text-primary font-medium hover:underline"
          >
            注册
          </button>
        </p>
      </div>
    </div>
  )
}
