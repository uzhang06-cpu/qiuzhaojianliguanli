import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Merge Tailwind classes with conflict resolution. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Format ISO datetime to Chinese locale string. */
export function formatTime(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Check if a DDL is urgent (< 2h) or soon (< 24h). */
export function getDDLUrgency(iso?: string): 'urgent' | 'soon' | 'normal' {
  if (!iso) return 'normal'
  const now = Date.now()
  const ddl = new Date(iso).getTime()
  const diff = ddl - now
  if (diff < 0) return 'normal'
  if (diff < 2 * 60 * 60 * 1000) return 'urgent'
  if (diff < 24 * 60 * 60 * 1000) return 'soon'
  return 'normal'
}

/** Get status color class for a pipeline stage. */
export function getStatusColor(key: string): string {
  const colors: Record<string, string> = {
    interested: '#6366f1',
    applied: '#3b82f6',
    assessment: '#f59e0b',
    ai_interview: '#8b5cf6',
    human_interview: '#06b6d4',
    offer_evaluation: '#22c55e',
    archived: '#6b7280',
  }
  return colors[key] || '#6b7280'
}
