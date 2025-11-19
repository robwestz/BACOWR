'use client'

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { batchReviewAPI } from '@/lib/api/client'
import { formatRelativeTime } from '@/lib/utils/format'
import {
  Search,
  Plus,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  Package,
  TrendingUp,
} from 'lucide-react'
import Link from 'next/link'
import type { BatchReviewStatus } from '@/types'

const STATUS_CONFIG: Record<
  BatchReviewStatus,
  { label: string; color: string; icon: React.ComponentType<any> }
> = {
  pending: { label: 'Pending', color: 'bg-gray-500', icon: Clock },
  processing: { label: 'Processing', color: 'bg-blue-500', icon: Clock },
  ready_for_review: { label: 'Ready for Review', color: 'bg-yellow-500', icon: AlertCircle },
  in_review: { label: 'In Review', color: 'bg-orange-500', icon: Package },
  completed: { label: 'Completed', color: 'bg-green-500', icon: CheckCircle2 },
  failed: { label: 'Failed', color: 'bg-red-500', icon: XCircle },
}

export default function BatchesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<BatchReviewStatus | 'all'>('all')
  const [page, setPage] = useState(1)

  const { data: batchesData, isLoading, refetch } = useQuery({
    queryKey: ['batches', page, statusFilter],
    queryFn: () =>
      batchReviewAPI.list({
        page,
        per_page: 20,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      }),
  })

  const batches = batchesData?.batches || []
  const total = batchesData?.total || 0

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    )
  }

  const filteredBatches = searchQuery
    ? batches.filter(
        (batch) =>
          batch.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          batch.description?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : batches

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Batch Review</h1>
          <p className="text-muted-foreground mt-1">
            Review and approve batches of generated articles (Day 2 QA)
          </p>
        </div>
        <Link href="/batches/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Batch
          </Button>
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Batches</p>
                <p className="text-2xl font-bold">{total}</p>
              </div>
              <Package className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Ready for Review</p>
                <p className="text-2xl font-bold">
                  {batches.filter((b) => b.status === 'ready_for_review').length}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">In Review</p>
                <p className="text-2xl font-bold">
                  {batches.filter((b) => b.status === 'in_review').length}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold">
                  {batches.filter((b) => b.status === 'completed').length}
                </p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search batches..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={statusFilter === 'all' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('all')}
                size="sm"
              >
                All
              </Button>
              <Button
                variant={statusFilter === 'ready_for_review' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('ready_for_review')}
                size="sm"
              >
                Ready for Review
              </Button>
              <Button
                variant={statusFilter === 'in_review' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('in_review')}
                size="sm"
              >
                In Review
              </Button>
              <Button
                variant={statusFilter === 'completed' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('completed')}
                size="sm"
              >
                Completed
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Batches Table */}
      <Card>
        <CardHeader>
          <CardTitle>Batches</CardTitle>
          <CardDescription>
            Click on a batch to review its items
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredBatches.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No batches found</p>
                <p className="text-sm">Create a batch from completed jobs to get started</p>
              </div>
            ) : (
              filteredBatches.map((batch) => {
                const StatusIcon = STATUS_CONFIG[batch.status].icon
                const approvalRate =
                  batch.stats.total_items > 0
                    ? Math.round((batch.stats.approved / batch.stats.total_items) * 100)
                    : 0

                return (
                  <Link
                    key={batch.id}
                    href={`/batches/${batch.id}/review`}
                    className="block"
                  >
                    <div className="border rounded-lg p-4 hover:border-primary hover:bg-accent/50 transition-all cursor-pointer">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold text-lg truncate">
                              {batch.name}
                            </h3>
                            <Badge
                              className={`${STATUS_CONFIG[batch.status].color} text-white`}
                            >
                              <StatusIcon className="h-3 w-3 mr-1" />
                              {STATUS_CONFIG[batch.status].label}
                            </Badge>
                          </div>
                          {batch.description && (
                            <p className="text-sm text-muted-foreground mb-3">
                              {batch.description}
                            </p>
                          )}
                          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-sm">
                            <div>
                              <p className="text-muted-foreground">Total Items</p>
                              <p className="font-medium">{batch.stats.total_items}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Approved</p>
                              <p className="font-medium text-green-600">
                                {batch.stats.approved}
                              </p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Rejected</p>
                              <p className="font-medium text-red-600">
                                {batch.stats.rejected}
                              </p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Pending</p>
                              <p className="font-medium text-yellow-600">
                                {batch.stats.pending}
                              </p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Approval Rate</p>
                              <p className="font-medium">{approvalRate}%</p>
                            </div>
                          </div>
                        </div>
                        <div className="text-right ml-4">
                          <p className="text-sm text-muted-foreground">
                            Created {formatRelativeTime(batch.created_at)}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">
                            {batch.job_ids.length} jobs
                          </p>
                        </div>
                      </div>
                    </div>
                  </Link>
                )
              })
            )}
          </div>

          {/* Pagination */}
          {total > 20 && (
            <div className="flex items-center justify-between mt-6 pt-6 border-t">
              <p className="text-sm text-muted-foreground">
                Showing {((page - 1) * 20) + 1}-{Math.min(page * 20, total)} of {total} batches
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page * 20 >= total}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
