import { useState } from 'react'
import { useAuthStore } from '@/store/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/toast'
import { Briefcase, Loader2 } from 'lucide-react'

interface RegisterPageProps {
  onNavigateToLogin: () => void
  onRegisterSuccess: () => void
}

export function RegisterPage({ onNavigateToLogin, onRegisterSuccess }: RegisterPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password) return
    if (password !== confirm) {
      toast.error('两次密码不一致')
      return
    }
    if (password.length < 6) {
      toast.error('密码至少 6 位')
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '注册失败')
      }
      const data = await res.json()
      setAuth(data.access_token, data.user)
      toast.success('注册成功')
      onRegisterSuccess()
    } catch (e: any) {
      toast.error(e.message || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center">
          <span className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-primary text-primary-foreground mb-4">
            <Briefcase className="w-6 h-6" />
          </span>
          <h1 className="text-xl font-semibold">创建账号</h1>
          <p className="text-sm text-muted-foreground mt-1">注册 SmartTracker</p>
        </div>

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
            <Input
              type="password"
              placeholder="至少 6 位"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">确认密码</label>
            <Input
              type="password"
              placeholder="再次输入密码"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
          </div>

          <Button type="submit" className="w-full h-10" disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            {loading ? '注册中...' : '注册'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          已有账号？{' '}
          <button
            onClick={onNavigateToLogin}
            className="text-primary font-medium hover:underline"
          >
            登录
          </button>
        </p>
      </div>
    </div>
  )
}
