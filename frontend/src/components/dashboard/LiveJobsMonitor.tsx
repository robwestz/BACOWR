'use client'

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { JobProgressBar } from '@/components/jobs/JobProgressBar'
import { Activity } from 'lucide-react'
import { useWebSocket } from '@/lib/api/websocket'
import { useJobsStore } from '@/lib/store'
import type { WSJobUpdate } from '@/types'

export function LiveJobsMonitor() {
  const { connect, on, off } = useWebSocket()
  const activeJobs = useJobsStore((state) => state.activeJobs)
  const updateJob = useJobsStore((state) => state.updateJob)

  const [liveUpdates, setLiveUpdates] = useState<Map<string, WSJobUpdate>>(
    new Map()
  )

  useEffect(() => {
    connect()

    const handleUpdate = (update: WSJobUpdate) => {
      setLiveUpdates((prev) => new Map(prev).set(update.job_id, update))
      updateJob(update.job_id, { job_meta: { status: update.status } as any })
    }

    on('job:update', handleUpdate)

    return () => {
      off('job:update', handleUpdate)
    }
  }, [connect, on, off, updateJob])

  const runningJobs = Array.from(activeJobs.values()).filter(
    (job) => job.job_meta.status === 'RUNNING' || job.job_meta.status === 'PENDING'
  )

  if (runningJobs.length === 0) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary animate-pulse" />
          <CardTitle>Live Jobs</CardTitle>
          <Badge variant="secondary">{runningJobs.length} active</Badge>
        </div>
        <CardDescription>Real-time job status updates</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {runningJobs.map((job) => {
          const update = liveUpdates.get(job.job_meta.job_id)
          return (
            <JobProgressBar
              key={job.job_meta.job_id}
              jobId={job.job_meta.job_id}
              status={job.job_meta.status}
              progress={update?.progress || 0}
              message={update?.message}
              compact
            />
          )
        })}
      </CardContent>
    </Card>
  )
}
