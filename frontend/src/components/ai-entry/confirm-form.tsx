import { useState } from 'react'
import { AgentResult } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { CheckCircle2, AlertTriangle, Loader2, Brain, Sparkles } from 'lucide-react'

interface ConfirmFormProps {
  result: AgentResult
  onConfirm: (edited: Record<string, any>) => void
  onCancel: () => void
  isLoading?: boolean
}

export function ConfirmForm({ result, onConfirm, onCancel, isLoading }: ConfirmFormProps) {
  const [edits, setEdits] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {}
    result.display_fields.forEach((f) => { initial[f.key] = f.value })
    return initial
  })

  const avgConfidence =
    result.display_fields.length > 0
      ? result.display_fields.reduce((s, f) => s + f.confidence, 0) / result.display_fields.length
      : 0

  return (
    <Card className="animate-scale-in border-primary/10 shadow-[0_4px_16px_-4px_rgb(0_0_0/0.08)]">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10">
              <Brain className="w-4 h-4 text-primary" />
            </span>
            <div>
              <CardTitle>AI 解析结果</CardTitle>
              <CardDescription>请确认提取的信息，可直接编辑修正</CardDescription>
            </div>
          </div>
          <span
            className={cn(
              'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold',
              avgConfidence > 0.6 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700',
            )}
          >
            <Sparkles className="w-3 h-3" />
            置信度 {Math.round(avgConfidence * 100)}%
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-3.5">
        {result.display_fields.map((field) => (
          <div key={field.key} className="space-y-1.5">
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-muted-foreground">
                {field.label}
              </label>
              {field.highlight && (
                <span className="inline-flex items-center gap-0.5 text-[10px] text-amber-600 font-medium">
                  <AlertTriangle className="w-3 h-3" />
                  需确认
                </span>
              )}
              {field.confidence > 0.6 ? (
                <CheckCircle2 className="w-3 h-3 text-emerald-500 ml-auto" />
              ) : (
                <AlertTriangle className="w-3 h-3 text-amber-500 ml-auto" />
              )}
            </div>
            <Input
              value={edits[field.key] ?? ''}
              onChange={(e) => setEdits((prev) => ({ ...prev, [field.key]: e.target.value }))}
              className={cn(
                'h-9 text-sm',
                field.highlight && 'border-amber-300 focus-visible:ring-amber-200',
              )}
            />
          </div>
        ))}

        {result.needs_human_review && (
          <div className="flex items-start gap-3 rounded-lg bg-amber-50 border border-amber-200 p-3.5">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">需要人工确认</p>
              <p className="text-xs text-amber-600 mt-0.5">{result.human_review_reason}</p>
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-end gap-2 pt-1 pb-5">
        <Button variant="outline" size="sm" onClick={onCancel}>
          取消
        </Button>
        <Button size="sm" onClick={() => onConfirm(edits)} disabled={isLoading} className="gap-1.5">
          {isLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5" />
          )}
          {isLoading ? '提交中...' : '确认录入'}
        </Button>
      </CardFooter>
    </Card>
  )
}
