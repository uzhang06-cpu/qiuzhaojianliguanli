/**
 * 复盘列表页 — 所有已保存复盘笔记的集中查看/编辑入口。
 *
 * 从 store 中筛选出有 notes 的岗位，卡片式布局展示。
 * 点击卡片展开内联编辑。
 */
import { useState } from 'react'
import { usePositionStore } from '@/store/positions'
import { api } from '@/lib/api'
import { EmptyState } from '@/components/ui/empty-state'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { cn, formatTime } from '@/lib/utils'
import { FileText, Edit2, Save, X, ChevronLeft } from 'lucide-react'

export function ReviewsPage() {
  const positions = usePositionStore((s) => s.positions)
  const fetchPositions = usePositionStore((s) => s.fetchPositions)

  // Filter: only positions with notes
  const withNotes = positions.filter((p) => p.notes?.trim())

  // Edit state
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editText, setEditText] = useState('')
  const [saving, setSaving] = useState(false)

  const startEdit = (id: number, notes: string) => {
    setEditingId(id)
    setEditText(notes || '')
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditText('')
  }

  const saveEdit = async (id: number) => {
    if (!editText.trim() || saving) return
    setSaving(true)
    try {
      await api.updatePosition(id, { notes: editText.trim() })
      await fetchPositions()
      toast.success('复盘笔记已更新')
      setEditingId(null)
    } catch {
      toast.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  // Also show positions without notes that can use the review prompt
  const emptyNotes = positions.filter((p) => !p.notes?.trim() && p.next_ddl)

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="h-14 border-b bg-card flex items-center px-6 gap-3 sticky top-0 z-10">
        <button
          onClick={() => window.history.back()}
          className="p-1.5 rounded-md hover:bg-accent transition-colors"
          aria-label="返回"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <h1 className="text-sm font-semibold">复盘笔记</h1>
        <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
          {withNotes.length} 条记录
        </span>
      </header>

      <main className="max-w-2xl mx-auto p-6 space-y-4">
        {/* Notes listing */}
        {withNotes.length === 0 ? (
          <EmptyState
            icon={<FileText className="w-12 h-12" />}
            title="还没有复盘笔记"
            description="面试结束后，在卡片上点击即可记录复盘内容"
          />
        ) : (
          withNotes.map((pos) => {
            const isEditing = editingId === pos.id
            const preview = pos.notes?.slice(0, 120) ?? ''
            const hasMore = (pos.notes?.length ?? 0) > 120

            return (
              <div
                key={pos.id}
                className={cn(
                  'rounded-xl border bg-card overflow-hidden transition-all duration-200',
                  isEditing && 'ring-2 ring-primary/20 shadow-md',
                )}
              >
                {/* Card header */}
                <div className="px-5 py-4 border-b flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold">{pos.company}</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">{pos.position}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-muted-foreground">
                      {formatTime(pos.updated_at)}
                    </span>
                    {!isEditing && (
                      <button
                        onClick={() => startEdit(pos.id, pos.notes ?? '')}
                        className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                        aria-label="编辑"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Body */}
                <div className="px-5 py-4">
                  {isEditing ? (
                    <div className="space-y-3">
                      <Textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        className="min-h-[120px] resize-y text-sm"
                        autoFocus
                      />
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" size="sm" onClick={cancelEdit} className="gap-1">
                          <X className="w-3.5 h-3.5" />
                          取消
                        </Button>
                        <Button size="sm" onClick={() => saveEdit(pos.id)} disabled={saving} className="gap-1">
                          <Save className="w-3.5 h-3.5" />
                          {saving ? '保存中...' : '保存'}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <p className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap line-clamp-4">
                        {preview}
                        {hasMore && (
                          <button
                            onClick={() => startEdit(pos.id, pos.notes ?? '')}
                            className="ml-1 text-primary text-xs hover:underline"
                          >
                            展开全文
                          </button>
                        )}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}

        {/* Divider if there are positions needing notes */}
        {emptyNotes.length > 0 && withNotes.length > 0 && (
          <div className="border-t pt-6 mt-8">
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              待补充复盘 ({emptyNotes.length})
            </h2>
            <div className="grid gap-3">
              {emptyNotes.slice(0, 5).map((pos) => (
                <div
                  key={pos.id}
                  className="flex items-center justify-between rounded-lg border border-dashed px-4 py-3"
                >
                  <div>
                    <span className="text-sm font-medium">{pos.company}</span>
                    <span className="text-xs text-muted-foreground ml-2">{pos.position}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => startEdit(pos.id, '')}
                    className="text-xs gap-1"
                  >
                    <Edit2 className="w-3 h-3" />
                    写复盘
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
