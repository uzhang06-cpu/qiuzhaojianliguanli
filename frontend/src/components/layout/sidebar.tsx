import { cn } from '@/lib/utils'
import { ViewMode } from '@/types'
import { LayoutDashboard, List, Bell, Settings, Briefcase, FileText, Menu, X } from 'lucide-react'

const NAV = [
  { key: 'kanban' as const, label: '看板视图', icon: LayoutDashboard },
  { key: 'list' as const, label: '列表视图', icon: List },
]

const PAGES = [
  { key: 'reviews' as const, label: '复盘笔记', icon: FileText },
]

interface SidebarProps {
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
  onNotificationClick?: () => void
  onNavigate?: (page: string) => void
  currentPage?: string
  /** Mobile: open/close state */
  mobileOpen?: boolean
  onMobileClose?: () => void
}

export function Sidebar({
  viewMode,
  onViewModeChange,
  onNotificationClick,
  onNavigate,
  currentPage,
  mobileOpen,
  onMobileClose,
}: SidebarProps) {
  const content = (
    <aside className={cn(
      'flex flex-col bg-card h-full',
      'w-56',
    )}>
      {/* Logo */}
      <div className="flex items-center justify-between gap-2.5 px-5 h-14 border-b shrink-0">
        <div className="flex items-center gap-2.5">
          <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-primary text-primary-foreground">
            <Briefcase className="w-3.5 h-3.5" />
          </span>
          <span className="font-semibold text-[15px]">SmartTracker</span>
        </div>
        {onMobileClose && (
          <button onClick={onMobileClose} className="p-1 rounded-md hover:bg-accent md:hidden">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Nav — Views */}
      <nav className="flex-1 p-3 space-y-0.5">
        <p className="px-3 py-2 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
          视图
        </p>
        {NAV.map((item) => (
          <button
            key={item.key}
            onClick={() => {
              onViewModeChange(item.key)
              onMobileClose?.()
            }}
            className={cn(
              'flex items-center gap-3 w-full px-3 h-9 rounded-lg text-sm font-medium transition-all',
              viewMode === item.key && currentPage !== 'reviews'
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground',
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </button>
        ))}

        <p className="px-3 py-2 pt-4 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
          页面
        </p>
        {PAGES.map((item) => (
          <button
            key={item.key}
            onClick={() => {
              onNavigate?.(item.key)
              onMobileClose?.()
            }}
            className={cn(
              'flex items-center gap-3 w-full px-3 h-9 rounded-lg text-sm font-medium transition-all',
              currentPage === item.key
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground',
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </button>
        ))}
      </nav>

      {/* Bottom */}
      <div className="p-3 border-t space-y-0.5">
        <button
          onClick={() => { onNotificationClick?.(); onMobileClose?.() }}
          className="flex items-center gap-3 w-full px-3 h-9 rounded-lg text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
        >
          <Bell className="w-4 h-4" />
          通知中心
        </button>
      </div>
    </aside>
  )

  return (
    <>
      {/* Desktop: fixed sidebar */}
      <div className="hidden md:block fixed left-0 top-0 z-30 h-screen">{content}</div>

      {/* Mobile: overlay drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onMobileClose} />
          <div className="fixed left-0 top-0 h-full w-56 animate-slide-up shadow-2xl z-50">
            {content}
          </div>
        </div>
      )}

      {/* Mobile hamburger */}
      <button
        onClick={() => onMobileClose?.()}
        className="fixed bottom-4 left-4 z-30 md:hidden flex items-center justify-center w-12 h-12 rounded-full bg-primary text-primary-foreground shadow-lg"
        aria-label="菜单"
      >
        <Menu className="w-5 h-5" />
      </button>
    </>
  )
}
