import { usePositionStore } from '@/store/positions'
import { Badge } from '@/components/ui/badge'
import { cn, formatTime } from '@/lib/utils'
import { Bell, X, AlertTriangle, Info, CheckCircle, AlertCircle } from 'lucide-react'

const META = {
  danger: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-50' },
  warning: { icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-50' },
  info: { icon: Info, color: 'text-sky-500', bg: 'bg-sky-50' },
  success: { icon: CheckCircle, color: 'text-emerald-500', bg: 'bg-emerald-50' },
} as const

interface NotificationCenterProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function NotificationCenter({ open, onOpenChange }: NotificationCenterProps) {
  const notifications = usePositionStore((s) => s.notifications)
  const markRead = usePositionStore((s) => s.markNotifRead)
  const markAllRead = usePositionStore((s) => s.markAllNotifRead)
  const unread = notifications.filter((n) => !n.read).length

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" onClick={() => onOpenChange(false)} />
      <div className="relative w-[380px] bg-background border-l h-full shadow-2xl animate-slide-up flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-14 border-b shrink-0">
          <div className="flex items-center gap-2.5">
            <Bell className="w-4 h-4" />
            <span className="text-sm font-semibold">通知中心</span>
            {unread > 0 && (
              <span className="inline-flex items-center justify-center min-w-[20px] h-5 rounded-full bg-destructive text-[11px] font-semibold text-destructive-foreground px-1.5">
                {unread}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={markAllRead}
              className="text-[11px] text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-accent"
            >
              全部已读
            </button>
            <button
              onClick={() => onOpenChange(false)}
              className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-sm text-muted-foreground">
              <CheckCircle className="w-8 h-8 mb-2 text-emerald-400" />
              暂无新通知
            </div>
          ) : (
            notifications.map((n) => {
              const meta = META[n.type]
              const Icon = meta.icon
              return (
                <div
                  key={n.id}
                  onClick={() => markRead(n.id)}
                  className={cn(
                    'px-5 py-4 border-b border-border/50 transition-colors cursor-pointer',
                    'hover:bg-muted/20',
                    !n.read && 'bg-primary/[0.02]',
                  )}
                >
                  <div className="flex items-start gap-3">
                    <span className={cn('flex items-center justify-center w-8 h-8 rounded-lg shrink-0', meta.bg)}>
                      <Icon className={cn('w-4 h-4', meta.color)} />
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium">{n.title}</span>
                        {!n.read && <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{n.message}</p>
                      <span className="text-[11px] text-muted-foreground/60 mt-1.5 block">
                        {formatTime(n.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
