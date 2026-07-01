import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { Position, PIPELINE_STAGES } from '@/types'
import { PositionCard } from './position-card'
import { cn } from '@/lib/utils'

interface KanbanColumnProps {
  stage: (typeof PIPELINE_STAGES)[number]
  positions: Position[]
}

export function KanbanColumn({ stage, positions }: KanbanColumnProps) {
  const { isOver, setNodeRef } = useDroppable({ id: `column-${stage.key}` })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex flex-col rounded-xl min-w-[264px] w-[264px]',
        'bg-muted/40 border border-transparent',
        'transition-colors duration-150',
        isOver && 'column-drop-active',
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3.5 py-3 border-b border-border/50">
        <div className="flex items-center gap-2.5">
          <span
            className="w-2.5 h-2.5 rounded-full ring-2 ring-background"
            style={{ backgroundColor: stage.color }}
          />
          <h3 className="text-[13px] font-semibold">{stage.label}</h3>
        </div>
        <span className="inline-flex items-center justify-center min-w-[20px] h-5 rounded-full bg-muted text-[11px] font-medium text-muted-foreground px-1.5">
          {positions.length}
        </span>
      </div>

      {/* Cards */}
      <SortableContext
        items={positions.map((p) => p.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="flex-1 overflow-y-auto p-2 space-y-2 scrollbar-thin">
          {positions.length === 0 ? (
            <div className="flex items-center justify-center h-24 text-xs text-muted-foreground/60">
              暂无记录
            </div>
          ) : (
            positions.map((pos) => (
              <PositionCard key={pos.id} position={pos} />
            ))
          )}
        </div>
      </SortableContext>
    </div>
  )
}
