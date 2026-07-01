/**
 * Zustand store — SmartTracker global state.
 *
 * Manages position list, filters, loading states, and notifications.
 */
import { create } from 'zustand'
import { api, Position, PositionCreate, ListParams } from '@/lib/api'

/* ── Types ───────────────────────────────────────────────────────── */

type ViewMode = 'kanban' | 'list'

interface AppNotification {
  id: string
  type: 'warning' | 'danger' | 'info' | 'success'
  title: string
  message: string
  position_id?: number
  created_at: string
  read: boolean
}

interface PositionsState {
  // Data
  positions: Position[]
  notifications: AppNotification[]

  // UI state
  viewMode: ViewMode
  searchQuery: string
  statusFilter: string

  // Loading
  loading: boolean
  error: string | null

  // Actions
  setViewMode: (mode: ViewMode) => void
  setSearchQuery: (q: string) => void
  setStatusFilter: (s: string) => void

  fetchPositions: (params?: ListParams) => Promise<void>
  createPosition: (data: PositionCreate) => Promise<Position>
  transitionStatus: (id: number, newStatus: string, remark?: string) => Promise<void>
  updatePosition: (id: number, data: Partial<PositionCreate>) => Promise<void>
  deletePosition: (id: number) => Promise<void>

  markNotifRead: (id: string) => void
  markAllNotifRead: () => void
}

/* ── Store ────────────────────────────────────────────────────────── */

export const usePositionStore = create<PositionsState>((set, get) => ({
  // ── Initial state ──
  positions: [],
  notifications: [],
  viewMode: 'kanban',
  searchQuery: '',
  statusFilter: '',
  loading: false,
  error: null,

  // ── UI actions ──
  setViewMode: (mode) => set({ viewMode: mode }),
  setSearchQuery: (q) => set({ searchQuery: q }),
  setStatusFilter: (s) => set({ statusFilter: s }),

  // ── Data actions ──
  fetchPositions: async (params) => {
    set({ loading: true, error: null })
    try {
      const { searchQuery, statusFilter } = get()
      const list = await api.listPositions({
        keyword: params?.keyword || searchQuery || undefined,
        status: params?.status || statusFilter || undefined,
        sort_by: params?.sort_by,
        sort_dir: params?.sort_dir,
      })
      set({ positions: list, loading: false })
    } catch (e: any) {
      set({ error: e.message, loading: false })
    }
  },

  createPosition: async (data) => {
    const pos = await api.createPosition(data)
    await get().fetchPositions()
    return pos
  },

  transitionStatus: async (id, newStatus, remark) => {
    await api.transitionStatus(id, {
      status: newStatus,
      changed_by: 'user',
      remark,
    })
    await get().fetchPositions()
  },

  updatePosition: async (id, data) => {
    await api.updatePosition(id, data)
    await get().fetchPositions()
  },

  deletePosition: async (id) => {
    await api.deletePosition(id)
    await get().fetchPositions()
  },

  // ── Notifications ──
  markNotifRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) => (n.id === id ? { ...n, read: true } : n)),
    })),

  markAllNotifRead: () =>
    set((s) => ({
      notifications: s.notifications.map((n) => ({ ...n, read: true })),
    })),
}))
