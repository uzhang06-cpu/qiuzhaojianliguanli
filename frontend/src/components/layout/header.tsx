import { Search, Bell } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { ViewMode, PIPELINE_STAGES } from '@/types'

interface HeaderProps {
  viewMode: ViewMode
  searchQuery: string
  onSearchChange: (q: string) => void
  statusFilter: string
  onStatusFilterChange: (s: string) => void
  onNotificationClick?: () => void
}

export function Header({
  viewMode,
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  onNotificationClick,
}: HeaderProps) {
  return (
    <header className="h-14 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6 flex items-center gap-4 sticky top-0 z-20">
      {/* Search */}
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
        <Input
          placeholder="搜索公司、岗位..."
          className="pl-8 h-8 text-sm rounded-lg"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      {/* Status filter */}
      <select
        className="h-8 rounded-lg border border-input bg-background px-2.5 text-xs font-medium text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={statusFilter}
        onChange={(e) => onStatusFilterChange(e.target.value)}
      >
        <option value="">全部状态</option>
        {PIPELINE_STAGES.map((s) => (
          <option key={s.key} value={s.key}>
            {s.label}
          </option>
        ))}
      </select>

      {/* View indicator */}
      <span className="text-[11px] text-muted-foreground bg-muted px-2.5 py-1 rounded-full font-medium">
        {viewMode === 'kanban' ? '看板' : '列表'}
      </span>

      {/* Notification bell */}
      <button
        onClick={onNotificationClick}
        className="relative p-1.5 rounded-lg hover:bg-accent transition-colors"
        aria-label="通知中心"
      >
        <Bell className="w-4 h-4 text-muted-foreground" />
        <span className="notif-dot" />
      </button>
    </header>
  )
}
