import { useMemo, useState } from 'react'
import { usePositionStore } from '@/store/positions'
import { cn, formatTime, getDDLUrgency } from '@/lib/utils'
import { MapPin, Clock, ExternalLink, ArrowUpDown } from 'lucide-react'

type SortField = 'company' | 'next_ddl' | 'base_location' | 'updated_at'
type SortDir = 'asc' | 'desc'

export function PositionTable() {
  const { positions, searchQuery, statusFilter } = usePositionStore()
  const [sortField, setSortField] = useState<SortField>('updated_at')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const filtered = useMemo(() => {
    const q = searchQuery.toLowerCase()
    return positions.filter((p) => {
      if (statusFilter && p.status !== statusFilter) return false
      if (q && !p.company.toLowerCase().includes(q) && !p.position.toLowerCase().includes(q)) return false
      return true
    })
  }, [positions, searchQuery, statusFilter])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      let cmp = 0
      if (sortField === 'company') cmp = a.company.localeCompare(b.company)
      else if (sortField === 'next_ddl') cmp = (a.next_ddl ?? '').localeCompare(b.next_ddl ?? '')
      else if (sortField === 'base_location') cmp = (a.base_location ?? '').localeCompare(b.base_location ?? '')
      else cmp = new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [filtered, sortField, sortDir])

  const toggleSort = (field: SortField) => {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortField(field); setSortDir('asc') }
  }

  const SortHead = ({ field, label }: { field: SortField; label: string }) => (
    <th
      onClick={() => toggleSort(field)}
      className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider cursor-pointer hover:text-foreground select-none transition-colors"
    >
      <div className="flex items-center gap-1">
        {label}
        <ArrowUpDown className="w-3 h-3 opacity-40" />
      </div>
    </th>
  )

  return (
    <div className="rounded-xl border bg-card overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/30">
              <SortHead field="company" label="公司" />
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">岗位</th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">状态</th>
              <SortHead field="base_location" label="Base" />
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">薪资</th>
              <SortHead field="next_ddl" label="最近 DDL" />
              <SortHead field="updated_at" label="更新" />
              <th className="px-4 py-3 w-10" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-16 text-center text-sm text-muted-foreground">
                  暂无匹配的记录
                </td>
              </tr>
            ) : (
              sorted.map((pos) => {
                const urgency = getDDLUrgency(pos.next_ddl)
                return (
                  <tr key={pos.id} className="hover:bg-muted/20 transition-colors group">
                    <td className="px-4 py-3.5">
                      <span className="text-sm font-medium">{pos.company}</span>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-muted-foreground">{pos.position}</td>
                    <td className="px-4 py-3.5">
                      <span className={`badge-pipeline badge-pipeline-${pos.status}`}>
                        {pos.status_label}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-muted-foreground">
                      {pos.base_location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {pos.base_location}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-sm">{pos.salary_range || '—'}</td>
                    <td className="px-4 py-3.5">
                      <span className={cn(
                        'flex items-center gap-1 text-sm',
                        urgency === 'urgent' && 'ddl-urgent',
                        urgency === 'soon' && 'ddl-soon',
                        urgency === 'normal' && 'text-muted-foreground',
                      )}>
                        <Clock className="w-3 h-3" />
                        {pos.next_ddl ? formatTime(pos.next_ddl) : '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-muted-foreground">
                      {formatTime(pos.updated_at)}
                    </td>
                    <td className="px-4 py-3.5">
                      {pos.interview_link && (
                        <a
                          href={pos.interview_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center justify-center w-7 h-7 rounded-md text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-accent hover:text-foreground transition-all"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
