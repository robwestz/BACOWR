'use client'

import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { QuickStartWidget } from '@/components/dashboard/QuickStartWidget'
import { StatsCard } from '@/components/dashboard/StatsCard'
import { LiveJobsMonitor } from '@/components/dashboard/LiveJobsMonitor'
import { CostChart } from '@/components/dashboard/CostChart'
import { JobCard } from '@/components/jobs/JobCard'
import { statsAPI } from '@/lib/api/client'
import { FileText, CheckCircle2, XCircle, DollarSign, Clock } from 'lucide-react'
import { formatCurrency, formatDuration } from '@/lib/utils/format'

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => statsAPI.dashboard(),
  })

  const { data: costData } = useQuery({
    queryKey: ['cost-trends'],
    queryFn: () => statsAPI.costs({ group_by: 'day' }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome to BACOWR - Your SEO content generation platform
        </p>
      </div>

      {/* Quick Start + Live Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuickStartWidget />
        <LiveJobsMonitor />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Jobs"
          value={stats?.total_jobs || 0}
          icon={<FileText className="h-6 w-6" />}
        />
        <StatsCard
          title="Delivered"
          value={stats?.delivered || 0}
          icon={<CheckCircle2 className="h-6 w-6" />}
        />
        <StatsCard
          title="Total Cost"
          value={formatCurrency(stats?.total_cost || 0)}
          icon={<DollarSign className="h-6 w-6" />}
        />
        <StatsCard
          title="Avg Duration"
          value={formatDuration(stats?.avg_duration || 0)}
          icon={<Clock className="h-6 w-6" />}
        />
      </div>

      {/* Cost Chart */}
      {costData && (
        <CostChart
          data={
            costData.timeline?.map((item) => ({
              date: item.date,
              cost: item.cost,
            })) || []
          }
        />
      )}

      {/* Recent Jobs */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Recent Jobs</h2>
        {stats?.recent_jobs && stats.recent_jobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stats.recent_jobs.map((job) => (
              <JobCard key={job.job_meta.job_id} job={job} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No jobs yet. Create your first one using Quick Start above!</p>
          </div>
        )}
      </div>
    </div>
  )
}
