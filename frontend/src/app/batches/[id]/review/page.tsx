'use client'

import React, { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { batchReviewAPI } from '@/lib/api/client'
import { BatchReviewTable } from '@/components/batch/BatchReviewTable'
import { BatchFilters } from '@/components/batch/BatchFilters'
import { BulkActions } from '@/components/batch/BulkActions'
import { ArticlePreviewModal } from '@/components/batch/ArticlePreviewModal'
import {
  ArrowLeft,
  Download,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react'
import Link from 'next/link'
import type { BatchReviewItem, ReviewItemStatus } from '@/types'

export default function BatchReviewPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const batchId = params.id as string

  const [statusFilter, setStatusFilter] = useState<ReviewItemStatus | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const [previewItem, setPreviewItem] = useState<BatchReviewItem | null>(null)

  // Fetch batch details
  const { data: batch, isLoading: batchLoading } = useQuery({
    queryKey: ['batch', batchId],
    queryFn: () => batchReviewAPI.get(batchId),
  })

  // Fetch batch items
  const { data: itemsData, isLoading: itemsLoading } = useQuery({
    queryKey: ['batch-items', batchId, statusFilter],
    queryFn: () =>
      batchReviewAPI.getItems(batchId, {
        status: statusFilter !== 'all' ? statusFilter : undefined,
      }),
  })

  // Fetch batch stats
  const { data: stats } = useQuery({
    queryKey: ['batch-stats', batchId],
    queryFn: () => batchReviewAPI.getStats(batchId),
    refetchInterval: 10000, // Refetch every 10 seconds
  })

  // Review item mutation
  const reviewMutation = useMutation({
    mutationFn: ({
      itemId,
      decision,
      notes,
    }: {
      itemId: string
      decision: 'approve' | 'reject' | 'needs_regeneration'
      notes?: string
    }) =>
      batchReviewAPI.reviewItem(batchId, itemId, {
        decision,
        reviewer_notes: notes,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batch-items', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batch', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batch-stats', batchId] })
    },
  })

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: () => batchReviewAPI.exportBatch(batchId, 'json'),
    onSuccess: (data) => {
      // Download the export
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `batch-${batchId}-export.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })

  const items = itemsData?.items || []
  const filteredItems = searchQuery
    ? items.filter((item) =>
        item.job_id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : items

  // Handlers
  const handleToggleSelect = (itemId: string) => {
    const newSelected = new Set(selectedItems)
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId)
    } else {
      newSelected.add(itemId)
    }
    setSelectedItems(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedItems.size === filteredItems.length) {
      setSelectedItems(new Set())
    } else {
      setSelectedItems(new Set(filteredItems.map((item) => item.id)))
    }
  }

  const handleApprove = (itemId: string) => {
    reviewMutation.mutate({
      itemId,
      decision: 'approve',
    })
  }

  const handleReject = (itemId: string, notes?: string) => {
    reviewMutation.mutate({
      itemId,
      decision: 'reject',
      notes,
    })
  }

  const handleRequestRegeneration = (itemId: string, notes: string) => {
    reviewMutation.mutate({
      itemId,
      decision: 'needs_regeneration',
      notes,
    })
  }

  const handleBulkApprove = async () => {
    for (const itemId of selectedItems) {
      await reviewMutation.mutateAsync({
        itemId,
        decision: 'approve',
      })
    }
    setSelectedItems(new Set())
  }

  const handleBulkReject = async () => {
    for (const itemId of selectedItems) {
      await reviewMutation.mutateAsync({
        itemId,
        decision: 'reject',
      })
    }
    setSelectedItems(new Set())
  }

  const handleBulkExport = () => {
    const selectedItemsData = items.filter((item) => selectedItems.has(item.id))
    const exportData = {
      batch_id: batchId,
      batch_name: batch?.name || 'Unknown',
      export_date: new Date().toISOString(),
      selected_items: selectedItemsData.map((item) => ({
        job_id: item.job_id,
        article_text: item.qc_snapshot.article_text,
        qc_score: item.qc_snapshot.qc_score,
        word_count: item.qc_snapshot.word_count,
        review_status: item.review_status,
      })),
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `batch-${batchId}-selected-items.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (batchLoading || itemsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    )
  }

  if (!batch) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-xl font-semibold">Batch not found</p>
          <Link href="/batches">
            <Button className="mt-4">Back to Batches</Button>
          </Link>
        </div>
      </div>
    )
  }

  const approvalRate =
    batch.stats.total_items > 0
      ? Math.round((batch.stats.approved / batch.stats.total_items) * 100)
      : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link href="/batches">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Batches
          </Button>
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold">{batch.name}</h1>
            {batch.description && (
              <p className="text-muted-foreground mt-1">{batch.description}</p>
            )}
            <div className="flex items-center gap-4 mt-4">
              <Badge variant="outline">
                {batch.stats.total_items} items
              </Badge>
              <Badge className="bg-green-500 text-white">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                {batch.stats.approved} approved
              </Badge>
              <Badge className="bg-red-500 text-white">
                <XCircle className="h-3 w-3 mr-1" />
                {batch.stats.rejected} rejected
              </Badge>
              <Badge className="bg-yellow-500 text-white">
                <AlertTriangle className="h-3 w-3 mr-1" />
                {batch.stats.pending} pending
              </Badge>
            </div>
          </div>
          <Button
            onClick={() => exportMutation.mutate()}
            disabled={exportMutation.isPending || batch.stats.approved === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export Approved ({batch.stats.approved})
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Approval Rate</p>
                  <p className="text-2xl font-bold">{approvalRate}%</p>
                </div>
                <TrendingUp className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg QC Score</p>
                  <p className="text-2xl font-bold">
                    {Math.round(stats.quality_metrics.average_qc_score * 100)}
                  </p>
                </div>
                <CheckCircle2 className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Needs Regen</p>
                  <p className="text-2xl font-bold">
                    {batch.stats.needs_regeneration}
                  </p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Progress</p>
                  <p className="text-2xl font-bold">
                    {Math.round(
                      ((batch.stats.approved + batch.stats.rejected) /
                        batch.stats.total_items) *
                        100
                    )}
                    %
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <BatchFilters
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        showQCFilters={true}
      />

      {/* Bulk Actions */}
      <BulkActions
        selectedCount={selectedItems.size}
        onBulkApprove={handleBulkApprove}
        onBulkReject={handleBulkReject}
        onBulkExport={handleBulkExport}
        onClearSelection={() => setSelectedItems(new Set())}
        isLoading={reviewMutation.isPending}
      />

      {/* Review Table */}
      <Card>
        <CardHeader>
          <CardTitle>Review Items</CardTitle>
          <CardDescription>
            Review and approve/reject articles in this batch
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BatchReviewTable
            items={filteredItems}
            batchId={batchId}
            selectedItems={selectedItems}
            onToggleSelect={handleToggleSelect}
            onSelectAll={handleSelectAll}
            onViewItem={setPreviewItem}
            onApprove={handleApprove}
            onReject={handleReject}
            onRequestRegeneration={handleRequestRegeneration}
          />
        </CardContent>
      </Card>

      {/* Article Preview Modal */}
      <ArticlePreviewModal
        item={previewItem}
        isOpen={previewItem !== null}
        onClose={() => setPreviewItem(null)}
        onApprove={handleApprove}
        onReject={handleReject}
        onRequestRegeneration={handleRequestRegeneration}
      />
    </div>
  )
}
