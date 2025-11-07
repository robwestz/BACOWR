import React from 'react'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import type { JobStatus } from '@/types'

interface JobProgressBarProps {
  jobId: string
  status: JobStatus
  progress: number
  message?: string
  compact?: boolean
}

const statusConfig = {
  PENDING: {
    icon: Loader2,
    color: 'text-muted-foreground',
    label: 'Pending',
    variant: 'secondary' as const,
  },
  RUNNING: {
    icon: Loader2,
    color: 'text-blue-500',
    label: 'Running',
    variant: 'default' as const,
    animate: true,
  },
  DELIVERED: {
    icon: CheckCircle2,
    color: 'text-green-500',
    label: 'Delivered',
    variant: 'success' as const,
  },
  BLOCKED: {
    icon: AlertCircle,
    color: 'text-yellow-500',
    label: 'Blocked',
    variant: 'warning' as const,
  },
  ABORTED: {
    icon: XCircle,
    color: 'text-red-500',
    label: 'Aborted',
    variant: 'destructive' as const,
  },
}

export function JobProgressBar({
  jobId,
  status,
  progress,
  message,
  compact = false,
}: JobProgressBarProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <Icon
          className={`h-4 w-4 ${config.color} ${config.animate ? 'animate-spin' : ''}`}
        />
        <Progress value={progress} className="flex-1" />
        <Badge variant={config.variant}>{config.label}</Badge>
      </div>
    )
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon
                className={`h-5 w-5 ${config.color} ${config.animate ? 'animate-spin' : ''}`}
              />
              <span className="font-medium">{config.label}</span>
            </div>
            <Badge variant={config.variant}>{progress}%</Badge>
          </div>

          <Progress value={progress} />

          {message && (
            <p className="text-sm text-muted-foreground">{message}</p>
          )}

          <p className="text-xs text-muted-foreground font-mono">
            Job ID: {jobId}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
