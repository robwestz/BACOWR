import React from 'react'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, AlertCircle, XCircle } from 'lucide-react'
import type { QCStatus } from '@/types'

interface QCBadgeProps {
  status: QCStatus
  score?: number
  showIcon?: boolean
  className?: string
}

export function QCBadge({ status, score, showIcon = true, className }: QCBadgeProps) {
  const config = {
    PASS: {
      icon: CheckCircle2,
      label: 'Pass',
      variant: 'success' as const,
      color: 'text-green-500',
    },
    PASS_WITH_AUTOFIX: {
      icon: AlertCircle,
      label: 'Pass (Auto-fixed)',
      variant: 'warning' as const,
      color: 'text-yellow-500',
    },
    BLOCKED: {
      icon: XCircle,
      label: 'Blocked',
      variant: 'destructive' as const,
      color: 'text-red-500',
    },
  }

  const { icon: Icon, label, variant, color } = config[status]

  return (
    <Badge variant={variant} className={className}>
      {showIcon && <Icon className={`h-3 w-3 mr-1 ${color}`} />}
      {label}
      {score !== undefined && ` (${score}/100)`}
    </Badge>
  )
}
