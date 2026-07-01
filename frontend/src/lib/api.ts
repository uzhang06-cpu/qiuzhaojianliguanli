/**
 * SmartTracker API Client
 *
 * 开发环境通过 Vite proxy (/api → http://localhost:8000)
 * 生产环境通过 VITE_API_BASE 环境变量指向 Render 后端
 */

const BASE = (import.meta.env.VITE_API_BASE || '') + '/api'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const url = `${BASE}${path}`
  const headers: Record<string, string> = {}
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, detail.detail || res.statusText)
  }

  // 204 No Content
  if (res.status === 204) return undefined as T
  return res.json()
}

// ── Position APIs ─────────────────────────────────────────────────

export interface Position {
  id: number
  company: string
  position: string
  status: string
  status_label: string
  base_location?: string
  salary_range?: string
  job_description?: string
  next_ddl?: string
  interview_link?: string
  interview_platform?: string
  notes?: string
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface PositionCreate {
  company: string
  position: string
  status?: string
  base_location?: string
  salary_range?: string
  job_description?: string
  next_ddl?: string
  interview_link?: string
  interview_platform?: string
  notes?: string
}

export interface PositionUpdate {
  company?: string
  position?: string
  base_location?: string
  salary_range?: string
  job_description?: string
  next_ddl?: string
  interview_link?: string
  interview_platform?: string
  notes?: string
}

export interface StatusUpdate {
  status: string
  changed_by: string
  remark?: string
}

export interface ListParams {
  status?: string
  keyword?: string
  is_active?: boolean
  sort_by?: string
  sort_dir?: string
}

export const api = {
  // ── Positions ──

  listPositions(params?: ListParams): Promise<Position[]> {
    const q = new URLSearchParams()
    if (params?.status) q.set('status', params.status)
    if (params?.keyword) q.set('keyword', params.keyword)
    if (params?.is_active !== undefined) q.set('is_active', String(params.is_active))
    if (params?.sort_by) q.set('sort_by', params.sort_by)
    if (params?.sort_dir) q.set('sort_dir', params.sort_dir)
    const query = q.toString()
    return request<Position[]>('GET', `/positions${query ? `?${query}` : ''}`)
  },

  getPosition(id: number): Promise<Position> {
    return request<Position>('GET', `/positions/${id}`)
  },

  createPosition(data: PositionCreate): Promise<Position> {
    return request<Position>('POST', '/positions', data)
  },

  updatePosition(id: number, data: PositionUpdate): Promise<Position> {
    return request<Position>('PATCH', `/positions/${id}`, data)
  },

  transitionStatus(id: number, data: StatusUpdate): Promise<Position> {
    return request<Position>('POST', `/positions/${id}/status`, data)
  },

  deletePosition(id: number): Promise<void> {
    return request<void>('DELETE', `/positions/${id}`)
  },

  // ── Agent ──

  agentParse(text: string): Promise<{ success: boolean; data: any; conversation_id: number; message: string }> {
    return request('POST', '/agent/parse', { text })
  },

  // ── Status Logs ──

  listStatusLogs(position_id?: number, limit = 50): Promise<any[]> {
    const q = new URLSearchParams()
    if (position_id) q.set('position_id', String(position_id))
    q.set('limit', String(limit))
    return request('GET', `/status-logs?${q}`)
  },
}
