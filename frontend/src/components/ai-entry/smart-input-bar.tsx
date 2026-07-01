import { useState, useRef, useEffect } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Loader2, Sparkles, X, CornerDownLeft } from 'lucide-react'

interface SmartInputBarProps {
  onSubmit: (text: string) => void
  isLoading: boolean
}

export function SmartInputBar({ onSubmit, isLoading }: SmartInputBarProps) {
  const [text, setText] = useState('')
  const [expanded, setExpanded] = useState(false)
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (expanded && ref.current) ref.current.focus()
  }, [expanded])

  const submit = () => {
    if (!text.trim() || isLoading) return
    onSubmit(text.trim())
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit()
    if (e.key === 'Escape') { setExpanded(false); setText('') }
  }

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full flex items-center gap-3 rounded-xl border-2 border-dashed border-border px-4 py-3 text-left cursor-pointer hover:border-primary/30 hover:bg-primary/[0.02] transition-all group"
      >
        <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 text-primary shrink-0">
          <Sparkles className="w-4 h-4" />
        </span>
        <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
          AI 闪电录入 — 粘贴 JD 或面试通知，一键解析...
        </span>
        <span className="ml-auto text-[11px] text-muted-foreground/50 hidden sm:inline">
          ⌘K
        </span>
      </button>
    )
  }

  return (
    <div className="rounded-xl border bg-card shadow-[0_4px_16px_-4px_rgb(0_0_0/0.08)] animate-scale-in overflow-hidden">
      <div className="p-4">
        <Textarea
          ref={ref}
          placeholder="粘贴 JD 文本、面试通知、HR 消息..."
          className="min-h-[100px] resize-none border-0 focus-visible:ring-0 p-0 text-sm placeholder:text-muted-foreground/50"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
        />
      </div>
      <div className="flex items-center justify-between px-4 py-2.5 bg-muted/30 border-t">
        <button
          onClick={() => { setExpanded(false); setText('') }}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-accent"
        >
          <X className="w-3.5 h-3.5" />
          取消
        </button>
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-muted-foreground">{text.length} 字符</span>
          <Button
            size="sm"
            onClick={submit}
            disabled={!text.trim() || isLoading}
            className="gap-1.5"
          >
            {isLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            {isLoading ? '解析中...' : 'AI 解析'}
            {!isLoading && <CornerDownLeft className="w-3 h-3 opacity-60" />}
          </Button>
        </div>
      </div>
    </div>
  )
}
