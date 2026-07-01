import { useMemo, useCallback } from 'react'
import {
  DndContext,
  DragOverlay,
  DragStartEvent,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { usePositionStore } from '@/store/positions'
import { Position, PIPELINE_STAGES } from '@/types'
import { KanbanColumn } from './kanban-column'
import { toast } from '@/components/ui/toast'

export function KanbanBoard() {
  const { positions, searchQuery, statusFilter, transitionStatus } = usePositionStore()

  // Filter positions based on search + status filter
  const filtered = useMemo(() => {
    const q = searchQuery.toLowerCase()
    return positions.filter((p) => {
      if (statusFilter && p.status !== statusFilter) return false
      if (q && !p.company.toLowerCase().includes(q) && !p.position.toLowerCase().includes(q)) return false
      return true
    })
  }, [positions, searchQuery, statusFilter])

  // Group by pipeline stage
  const grouped = useMemo(() => {
    const map = new Map(PIPELINE_STAGES.map((s) => [s.key, [] as Position[]]))
    filtered.forEach((p) => map.get(p.status)?.push(p))
    return map
  }, [filtered])

  // Drag state
  const activeId = null // local state if needed

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  )

  const handleDragEnd = useCallback(
    async (e: DragEndEvent) => {
      const { active, over } = e
      if (!over || !over.id.toString().startsWith('column-')) return

      const targetStage = over.id.toString().replace('column-', '')
      const pos = positions.find((p) => p.id === active.id)
      if (pos && pos.status !== targetStage) {
        try {
          await transitionStatus(pos.id, targetStage, `拖拽变更: ${pos.status} → ${targetStage}`)
          toast.success(`${pos.company} 状态已更新`)
        } catch (err) {
          toast.error('状态变更失败')
        }
      }
    },
    [positions, transitionStatus],
  )

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-4" style={{ height: 'calc(100vh - 210px)' }}>
        {PIPELINE_STAGES.map((stage) => (
          <KanbanColumn
            key={stage.key}
            stage={stage}
            positions={grouped.get(stage.key) ?? []}
          />
        ))}
      </div>
      <DragOverlay dropAnimation={null}>
        {/* Active card overlay here */}
      </DragOverlay>
    </DndContext>
  )
}
