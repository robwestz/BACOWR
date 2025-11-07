import React from 'react'
import Link from 'next/link'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatRelativeTime, formatCurrency } from '@/lib/utils/format'
import { ExternalLink, FileText, MoreVertical } from 'lucide-react'
import type { JobPackage } from '@/types'

interface JobCardProps {
  job: JobPackage
  onViewDetails?: () => void
  onDelete?: () => void
}

export function JobCard({ job, onViewDetails, onDelete }: JobCardProps) {
  const { job_meta, input_minimal, qc_report, metrics } = job

  const statusColors = {
    PENDING: 'secondary',
    RUNNING: 'warning',
    DELIVERED: 'success',
    BLOCKED: 'destructive',
    ABORTED: 'destructive',
  } as const

  const qcStatusColors = {
    PASS: 'success',
    PASS_WITH_AUTOFIX: 'warning',
    BLOCKED: 'destructive',
  } as const

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold">
              {input_minimal.publisher_domain}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-1">
              {input_minimal.anchor_text}
            </p>
          </div>
          <Badge variant={statusColors[job_meta.status]}>
            {job_meta.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="flex items-center gap-2 text-sm">
          <ExternalLink className="h-4 w-4 text-muted-foreground" />
          <a
            href={input_minimal.target_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline truncate"
          >
            {new URL(input_minimal.target_url).hostname}
          </a>
        </div>

        {qc_report && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">QC:</span>
            <Badge variant={qcStatusColors[qc_report.status]} size="sm">
              {qc_report.status}
            </Badge>
            <span className="text-sm text-muted-foreground">
              Score: {qc_report.overall_score}/100
            </span>
          </div>
        )}

        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{formatRelativeTime(job_meta.created_at)}</span>
          {metrics?.generation?.cost_usd && (
            <span className="font-medium">
              {formatCurrency(metrics.generation.cost_usd)}
            </span>
          )}
        </div>
      </CardContent>

      <CardFooter className="pt-0 flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1"
          onClick={onViewDetails}
          asChild
        >
          <Link href={`/jobs/${job_meta.job_id}`}>
            <FileText className="h-4 w-4 mr-2" />
            View Details
          </Link>
        </Button>
      </CardFooter>
    </Card>
  )
}
