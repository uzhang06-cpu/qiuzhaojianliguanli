/**
 * Auth Store — JWT 登录状态管理。
 *
 * token 存 localStorage，页面刷新后自动恢复。
 */
import { create } from 'zustand'

interface User {
  id: number
  email: string
  created_at: string
}

interface AuthState {
  token: string | null
  user: User | null
  loading: boolean

  setAuth: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: () => boolean
}

// 从 localStorage 恢复
const savedToken = localStorage.getItem('smarttracker_token')
const savedUser = localStorage.getItem('smarttracker_user')

export const useAuthStore = create<AuthState>((set, get) => ({
  token: savedToken,
  user: savedUser ? JSON.parse(savedUser) : null,
  loading: false,

  setAuth: (token, user) => {
    localStorage.setItem('smarttracker_token', token)
    localStorage.setItem('smarttracker_user', JSON.stringify(user))
    set({ token, user })
  },

  logout: () => {
    localStorage.removeItem('smarttracker_token')
    localStorage.removeItem('smarttracker_user')
    set({ token: null, user: null })
  },

  isAuthenticated: () => get().token !== null,
}))
