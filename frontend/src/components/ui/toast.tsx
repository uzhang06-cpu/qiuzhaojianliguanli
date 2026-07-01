/**
 * Toast 通知系统 — 轻量级、无外部依赖。
 *
 * 用法:
 *   toast.success('保存成功')
 *   toast.error('操作失败')
 *   toast.info('面试即将开始')
 */
import { useState, useEffect, useCallback } from 'react'
import { create } from 'zustand'
import { cn } from '@/lib/utils'
import { CheckCircle, AlertCircle, AlertTriangle, Info, X } from 'lucide-react'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: number
  type: ToastType
  message: string
}

const META = {
  success: { icon: CheckCircle, bg: 'bg-emerald-50 border-emerald-200 text-emerald-800', dark: 'dark:bg-emerald-950 dark:border-emerald-800 dark:text-emerald-400' },
  error: { icon: AlertCircle, bg: 'bg-red-50 border-red-200 text-red-800', dark: 'dark:bg-red-950 dark:border-red-800 dark:text-red-400' },
  warning: { icon: AlertTriangle, bg: 'bg-amber-50 border-amber-200 text-amber-800', dark: 'dark:bg-amber-950 dark:border-amber-800 dark:text-amber-400' },
  info: { icon: Info, bg: 'bg-sky-50 border-sky-200 text-sky-800', dark: 'dark:bg-sky-950 dark:border-sky-800 dark:text-sky-400' },
}

// Global toast store
const useToastStore = create<{ toasts: Toast[]; push: (t: Toast) => void; remove: (id: number) => void }>((set) => ({
  toasts: [],
  push: (t) => set((s) => ({ toasts: [...s.toasts, t] })),
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))

let nextId = 1
const show = (type: ToastType, message: string) => {
  const id = nextId++
  useToastStore.getState().push({ id, type, message })
  setTimeout(() => useToastStore.getState().remove(id), 4000)
}

export const toast = {
  success: (msg: string) => show('success', msg),
  error: (msg: string) => show('error', msg),
  warning: (msg: string) => show('warning', msg),
  info: (msg: string) => show('info', msg),
}

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts)
  const remove = useToastStore((s) => s.remove)

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => {
        const meta = META[t.type]
        const Icon = meta.icon
        return (
          <div
            key={t.id}
            className={cn(
              'flex items-start gap-3 px-4 py-3 rounded-lg border shadow-lg animate-slide-up',
              meta.bg, meta.dark,
            )}
          >
            <Icon className="w-4 h-4 mt-0.5 shrink-0" />
            <p className="text-sm flex-1">{t.message}</p>
            <button onClick={() => remove(t.id)} className="p-0.5 rounded hover:opacity-70">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
