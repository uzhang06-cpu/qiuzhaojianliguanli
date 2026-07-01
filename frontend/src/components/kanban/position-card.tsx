import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Position } from '@/types'
import { cn, formatTime, getDDLUrgency } from '@/lib/utils'
import { MapPin, Clock, ExternalLink, AlertTriangle } from 'lucide-react'

interface PositionCardProps {
  position: Position
  isDragging?: boolean
}

export function PositionCard({ position, isDragging }: PositionCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: position.id,
  })

  const style = { transform: CSS.Transform.toString(transform), transition }
  const urgency = getDDLUrgency(position.next_ddl)

  const needsReview =
    position.status === 'human_interview' &&
    position.next_ddl &&
    new Date(position.next_ddl).getTime() < Date.now() - 2 * 60 * 60 * 1000

  // Stagnant detection: updated_at > 7 days in a non-terminal state
  const stagnantDays = (() => {
    const updated = new Date(position.updated_at).getTime()
    if (isNaN(updated)) return 0
    if (position.status === 'archived' || position.status === 'offer_evaluation') return 0
    const days = (Date.now() - updated) / (1000 * 60 * 60 * 24)
    return Math.floor(days)
  })()

  const isStagnant = stagnantDays >= 7

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        'group rounded-lg border bg-card p-3.5 cursor-grab active:cursor-grabbing',
        'transition-all duration-150 hover:shadow-md hover:-translate-y-[1px]',
        'select-none',
        isDragging && 'dragging shadow-lg',
        needsReview && 'opacity-60 hover:opacity-100',
      )}
    >
      {/* Company + Status line */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <h4 className="text-[13px] font-semibold leading-snug truncate">
            {position.company}
          </h4>
          <p className="text-[11px] text-muted-foreground truncate mt-0.5">
            {position.position}
          </p>
        </div>
        <span
          className={cn(
            'badge-pipeline shrink-0 mt-0.5',
            `badge-pipeline-${position.status}`,
          )}
        >
          {position.status_label}
        </span>
      </div>

      {/* Meta row */}
      <div className="flex items-center gap-2.5 text-[11px] text-muted-foreground mb-2">
        {position.base_location && (
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {position.base_location}
          </span>
        )}
        {position.salary_range && (
          <span className="font-medium text-foreground/60">{position.salary_range}</span>
        )}
      </div>

      {/* DDL + Link */}
      <div className="flex items-center justify-between border-t pt-2">
        <span
          className={cn(
            'flex items-center gap-1 text-[11px]',
            urgency === 'urgent' && 'ddl-urgent',
            urgency === 'soon' && 'ddl-soon',
            urgency === 'normal' && 'text-muted-foreground',
          )}
        >
          <Clock className="w-3 h-3" />
          {position.next_ddl ? formatTime(position.next_ddl) : '—'}
        </span>

        {position.interview_link && (
          <a
            href={position.interview_link}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-[11px] font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity hover:underline"
          >
            <ExternalLink className="w-3 h-3" />
            入会
          </a>
        )}
      </div>

      {/* Zombie state warning */}
      {isStagnant && (
        <div className="flex items-center gap-1.5 mt-2 pt-2 border-t border-dashed text-[10px] text-amber-600 font-medium">
          <AlertTriangle className="w-3 h-3" />
          已停滞 {stagnantDays} 天
        </div>
      )}
    </div>
  )
}
