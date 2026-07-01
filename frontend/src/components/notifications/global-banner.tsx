/**
 * Global Notification Banner
 *
 * Appears at the top of the page when there are urgent notifications.
 * Dismissable. Animates in/out.
 */
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { AlertTriangle, AlertCircle, Info, X } from 'lucide-react'

interface BannerItem {
  id: string
  severity: 'danger' | 'warning' | 'info'
  message: string
  type: string
}

const META = {
  danger: { icon: AlertCircle, bg: 'bg-red-50 border-red-200 text-red-800', dark: 'dark:bg-red-950 dark:border-red-800 dark:text-red-400' },
  warning: { icon: AlertTriangle, bg: 'bg-amber-50 border-amber-200 text-amber-800', dark: 'dark:bg-amber-950 dark:border-amber-800 dark:text-amber-400' },
  info: { icon: Info, bg: 'bg-sky-50 border-sky-200 text-sky-800', dark: 'dark:bg-sky-950 dark:border-sky-800 dark:text-sky-400' },
}

interface GlobalBannerProps {
  pollInterval?: number // ms, default 30000
}

export function GlobalBanner({ pollInterval = 30000 }: GlobalBannerProps) {
  const [items, setItems] = useState<BannerItem[]>([])
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await fetch('/api/notifications')
      if (!res.ok) return
      const data = await res.json()
      const banners: BannerItem[] = (data.notifications || [])
        .filter((n: any) => n.severity === 'danger' || n.severity === 'warning')
        .map((n: any) => ({
          id: `${n.type}-${n.position_id}`,
          severity: n.severity,
          message: n.message,
          type: n.type,
        }))
      setItems(banners)
    } catch {
      // silent — backend may not be running
    }
  }, [])

  // Poll on mount and on interval
  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, pollInterval)
    return () => clearInterval(interval)
  }, [fetchNotifications, pollInterval])

  const visible = items.filter((n) => !dismissed.has(n.id))
  if (visible.length === 0) return null

  return (
    <div className="space-y-2 animate-slide-down">
      {visible.map((item) => {
        const meta = META[item.severity]
        const Icon = meta.icon
        return (
          <div
            key={item.id}
            className={cn(
              'flex items-start gap-3 px-4 py-3 rounded-lg border shadow-sm',
              meta.bg,
              meta.dark,
            )}
          >
            <Icon className="w-4 h-4 mt-0.5 shrink-0" />
            <p className="text-sm flex-1">{item.message}</p>
            <button
              onClick={() => setDismissed((prev) => new Set(prev).add(item.id))}
              className="p-0.5 rounded hover:opacity-70 transition-opacity shrink-0"
              aria-label="关闭"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
