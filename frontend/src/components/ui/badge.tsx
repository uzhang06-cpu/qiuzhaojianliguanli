import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold leading-none transition-colors select-none',
  {
    variants: {
      variant: {
        default: 'bg-primary/10 text-primary',
        secondary: 'bg-secondary text-secondary-foreground',
        destructive: 'bg-destructive/10 text-destructive',
        outline: 'border text-foreground',
        success: 'bg-emerald-50 text-emerald-700',
        warning: 'bg-amber-50 text-amber-700',
        // Pipeline variants
        interested: 'badge-pipeline-interested',
        applied: 'badge-pipeline-applied',
        assessment: 'badge-pipeline-assessment',
        ai_interview: 'badge-pipeline-ai_interview',
        human_interview: 'badge-pipeline-human_interview',
        offer_evaluation: 'badge-pipeline-offer_evaluation',
        archived: 'badge-pipeline-archived',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
