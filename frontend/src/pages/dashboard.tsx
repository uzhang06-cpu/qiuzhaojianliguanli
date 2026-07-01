import { useEffect, useState, useRef, useCallback } from 'react'
import { usePositionStore } from '@/store/positions'
import { Sidebar } from '@/components/layout/sidebar'
import { Header } from '@/components/layout/header'
import { KanbanBoard } from '@/components/kanban/kanban-board'
import { PositionTable } from '@/components/list/position-table'
import { SmartInputBar } from '@/components/ai-entry/smart-input-bar'
import { ConfirmForm } from '@/components/ai-entry/confirm-form'
import { NotificationCenter } from '@/components/notifications/notification-center'
import { GlobalBanner } from '@/components/notifications/global-banner'
import { ReviewPrompt } from '@/components/notifications/review-prompt'
import { toast } from '@/components/ui/toast'
import { api } from '@/lib/api'
import type { AgentResult } from '@/types'

interface DashboardProps {
  onNavigate?: (page: string) => void
  currentPage?: string
}

export function Dashboard({ onNavigate, currentPage }: DashboardProps) {
  const store = usePositionStore()
  const [notifOpen, setNotifOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // AI entry state
  const [aiLoading, setAiLoading] = useState(false)
  const [aiResult, setAiResult] = useState<AgentResult | null>(null)
  const [aiConversationId, setAiConversationId] = useState(0)

  // Review prompt state
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewTarget, setReviewTarget] = useState<{ id: number; company: string; position: string } | null>(null)

  // Fetch positions on mount
  useEffect(() => {
    store.fetchPositions()
  }, [])

  // Debounced fetch when search/filter changes
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()
  const filterKey = `${store.searchQuery}::${store.statusFilter}`
  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      store.fetchPositions({
        keyword: store.searchQuery || undefined,
        status: store.statusFilter || undefined,
      })
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [filterKey])

  // AI: submit text to agent
  const handleAiSubmit = useCallback(async (text: string) => {
    setAiLoading(true)
    setAiResult(null)
    setAiConversationId(0)
    try {
      const res = await api.agentParse(text)
      if (res.success) {
        setAiResult(res.data)
        // @ts-ignore — API response may include conversation_id
        if (res.conversation_id) setAiConversationId(res.conversation_id)
      }
    } catch {
      setAiResult(mockParse(text))
    } finally {
      setAiLoading(false)
    }
  }, [])

  // AI: confirm → create + send corrections back for learning
  const handleAiConfirm = useCallback(async (edited: Record<string, any>) => {
    try {
      // Compute corrections (only if we have a real conversation)
      if (aiConversationId > 0 && aiResult) {
        const corrections: { field_name: string; original_value: string | null; corrected_value: string }[] = []
        for (const field of aiResult.display_fields) {
          const original = String(field.value ?? '')
          const corrected = String(edited[field.key] ?? '')
          if (original !== corrected) {
            corrections.push({ field_name: field.key, original_value: original, corrected_value: corrected })
          }
        }
        // Fire & forget — send corrections to learning backend
        if (corrections.length > 0) {
          fetch('/api/agent/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conversation_id: aiConversationId, session_id: 'default', corrections }),
          }).catch(() => {})
        }
      }

      await store.createPosition({
        company: edited.company || '未知公司',
        position: edited.position || '未知岗位',
        base_location: edited.base_location || undefined,
        salary_range: edited.salary_range || undefined,
        next_ddl: edited.next_ddl || undefined,
        interview_link: edited.interview_link || undefined,
        interview_platform: edited.interview_platform || undefined,
      })
      toast.success('岗位已添加')
      setAiResult(null)
    } catch (e) {
      toast.error('创建失败，请重试')
    }
  }, [store])

  // Review: save notes
  const handleReviewSubmit = useCallback(async (positionId: number, notes: string) => {
    await api.updatePosition(positionId, { notes })
    await store.fetchPositions()
  }, [store])

  return (
    <div className="min-h-screen">
      {/* Mobile hamburger toggle */}
      <button
        onClick={() => setMobileMenuOpen(true)}
        className="fixed bottom-4 left-4 z-30 md:hidden flex items-center justify-center w-12 h-12 rounded-full bg-primary text-primary-foreground shadow-lg"
        aria-label="菜单"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
      </button>

      <Sidebar
        viewMode={store.viewMode}
        onViewModeChange={store.setViewMode}
        onNotificationClick={() => setNotifOpen(true)}
        onNavigate={onNavigate}
        currentPage={currentPage}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      <div className="md:pl-56">
        <Header
          viewMode={store.viewMode}
          searchQuery={store.searchQuery}
          onSearchChange={store.setSearchQuery}
          statusFilter={store.statusFilter}
          onStatusFilterChange={store.setStatusFilter}
          onNotificationClick={() => setNotifOpen(true)}
        />

        <main className="p-6 space-y-4">
          {/* Global Notification Banner */}
          <GlobalBanner pollInterval={30000} />

          {/* AI Smart Input */}
          <SmartInputBar onSubmit={handleAiSubmit} isLoading={aiLoading} />

          {/* Loading indicator */}
          {store.loading && (
            <div className="flex items-center justify-center py-8">
              <div className="skeleton w-64 h-4" />
            </div>
          )}

          {/* Error */}
          {store.error && (
            <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
              {store.error}
            </div>
          )}

          {/* AI Confirm Form */}
          {aiResult && (
            <ConfirmForm
              result={aiResult}
              onConfirm={handleAiConfirm}
              onCancel={() => setAiResult(null)}
            />
          )}

          {/* Main view */}
          {!store.loading && !store.error && (
            store.viewMode === 'kanban' ? <KanbanBoard /> : <PositionTable />
          )}
        </main>
      </div>

      <NotificationCenter open={notifOpen} onOpenChange={setNotifOpen} />

      <ReviewPrompt
        open={reviewOpen}
        onOpenChange={setReviewOpen}
        company={reviewTarget?.company ?? ''}
        position={reviewTarget?.position ?? ''}
        positionId={reviewTarget?.id ?? 0}
        onSubmit={handleReviewSubmit}
      />
    </div>
  )
}

/* ── Offline mock for agent parse (no backend running) ──────────── */

function mockParse(text: string): AgentResult {
  const hasInterview = /面试|二面|一面|下周|明天/i.test(text)
  const hasCompany = /字节|阿里|腾讯|美团|百度/i.test(text)

  return {
    action_type: hasInterview ? 'update_interview' : 'create_position',
    action_label: hasInterview ? '更新面试信息' : '新增岗位线索',
    confidence: 0.75,
    display_fields: [
      {
        key: 'company',
        label: '公司名称',
        value: text.match(/字节|阿里|腾讯|美团|百度/i)?.[0] || '',
        confidence: 0.8,
        editable: true,
        highlight: !hasCompany,
      },
      {
        key: 'position',
        label: '岗位名称',
        value: '',
        confidence: 0.5,
        editable: true,
        highlight: true,
      },
      {
        key: 'base_location',
        label: 'Base 地',
        value: '',
        confidence: 0.5,
        editable: true,
        highlight: false,
      },
    ],
    needs_human_review: !hasCompany,
    human_review_reason: !hasCompany ? '未识别到公司名称，请手动补充' : '',
    raw_input: text,
    skill_results: [],
    total_latency_ms: 0,
  }
}
