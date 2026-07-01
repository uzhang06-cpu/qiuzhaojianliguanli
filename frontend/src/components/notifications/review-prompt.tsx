/**
 * Review Prompt Dialog
 *
 * Appears after an interview/assessment ends (> 2h) to prompt the user
 * to add notes/review before the details fade.
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogContent, DialogFooter } from '@/components/ui/dialog'
import { FileText, Sparkles } from 'lucide-react'

interface ReviewPromptProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  company: string
  position: string
  positionId: number
  onSubmit: (positionId: number, notes: string) => Promise<void>
}

export function ReviewPrompt({
  open,
  onOpenChange,
  company,
  position,
  positionId,
  onSubmit,
}: ReviewPromptProps) {
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!notes.trim() || submitting) return
    setSubmitting(true)
    try {
      await onSubmit(positionId, notes.trim())
      onOpenChange(false)
      setNotes('')
    } catch (e) {
      console.error('Failed to save notes:', e)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <div className="flex items-center gap-2.5">
          <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-sky-50 text-sky-600">
            <FileText className="w-4 h-4" />
          </span>
          <div>
            <DialogTitle>补充复盘笔记</DialogTitle>
            <DialogDescription>
              {company} — {position}
            </DialogDescription>
          </div>
        </div>
      </DialogHeader>

      <DialogContent>
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground leading-relaxed">
            面试刚结束，趁记忆犹新记录下面试官的问题、自己的表现和后续改进方向。
          </p>

          <div className="rounded-lg bg-sky-50 border border-sky-200 p-3 text-xs text-sky-700 space-y-1">
            <p className="font-medium flex items-center gap-1.5">
              <Sparkles className="w-3 h-3" />
              建议记录
            </p>
            <ul className="list-disc list-inside space-y-0.5 text-sky-600">
              <li>面试官问了哪些技术问题？</li>
              <li>哪些答得好，哪些需要加强？</li>
              <li>面试官的态度和风格？</li>
              <li>下一轮的预期时间？</li>
            </ul>
          </div>

          <Textarea
            placeholder="写下你的复盘内容..."
            className="min-h-[140px] resize-none"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
      </DialogContent>

      <DialogFooter>
        <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
          稍后再说
        </Button>
        <Button
          size="sm"
          onClick={handleSubmit}
          disabled={!notes.trim() || submitting}
          className="gap-1.5"
        >
          <FileText className="w-3.5 h-3.5" />
          {submitting ? '保存中...' : '保存复盘'}
        </Button>
      </DialogFooter>
    </Dialog>
  )
}
