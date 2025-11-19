'use client'

import React, { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Eye,
  RefreshCw,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import type { BatchReviewItem, ReviewItemStatus } from '@/types'

const STATUS_CONFIG: Record<
  ReviewItemStatus,
  { label: string; color: string; icon: React.ComponentType<any> }
> = {
  pending: { label: 'Pending', color: 'bg-gray-500', icon: AlertTriangle },
  approved: { label: 'Approved', color: 'bg-green-500', icon: CheckCircle2 },
  rejected: { label: 'Rejected', color: 'bg-red-500', icon: XCircle },
  needs_regeneration: { label: 'Needs Regen', color: 'bg-orange-500', icon: RefreshCw },
  regenerating: { label: 'Regenerating', color: 'bg-blue-500', icon: RefreshCw },
  regenerated: { label: 'Regenerated', color: 'bg-purple-500', icon: CheckCircle2 },
}

interface BatchReviewTableProps {
  items: BatchReviewItem[]
  batchId: string
  selectedItems: Set<string>
  onToggleSelect: (itemId: string) => void
  onSelectAll: () => void
  onViewItem: (item: BatchReviewItem) => void
  onApprove: (itemId: string) => void
  onReject: (itemId: string, notes?: string) => void
  onRequestRegeneration: (itemId: string, notes: string) => void
}

export function BatchReviewTable({
  items,
  batchId,
  selectedItems,
  onToggleSelect,
  onSelectAll,
  onViewItem,
  onApprove,
  onReject,
  onRequestRegeneration,
}: BatchReviewTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId)
    } else {
      newExpanded.add(itemId)
    }
    setExpandedRows(newExpanded)
  }

  const allSelected = items.length > 0 && selectedItems.size === items.length

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-3 bg-muted/50 rounded-t-lg border-b">
        <Checkbox checked={allSelected} onCheckedChange={onSelectAll} />
        <div className="grid grid-cols-12 gap-4 flex-1 text-sm font-medium">
          <div className="col-span-1">Status</div>
          <div className="col-span-3">Job ID</div>
          <div className="col-span-2">QC Score</div>
          <div className="col-span-2">Word Count</div>
          <div className="col-span-2">Issues</div>
          <div className="col-span-2">Actions</div>
        </div>
      </div>

      {/* Rows */}
      {items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>No items in this batch</p>
        </div>
      ) : (
        items.map((item) => {
          const StatusIcon = STATUS_CONFIG[item.review_status].icon
          const isExpanded = expandedRows.has(item.id)
          const isSelected = selectedItems.has(item.id)

          return (
            <Card key={item.id} className={isSelected ? 'border-primary' : ''}>
              <CardContent className="p-0">
                {/* Main Row */}
                <div className="flex items-center gap-4 px-4 py-3">
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => onToggleSelect(item.id)}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleExpanded(item.id)}
                    className="p-0 h-6 w-6"
                  >
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </Button>
                  <div className="grid grid-cols-12 gap-4 flex-1 items-center">
                    <div className="col-span-1">
                      <Badge
                        className={`${STATUS_CONFIG[item.review_status].color} text-white text-xs`}
                      >
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {STATUS_CONFIG[item.review_status].label}
                      </Badge>
                    </div>
                    <div className="col-span-3">
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {item.job_id.slice(0, 16)}...
                      </code>
                    </div>
                    <div className="col-span-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-2 w-full rounded-full overflow-hidden bg-muted`}
                        >
                          <div
                            className={`h-full ${
                              item.qc_snapshot.qc_score >= 0.8
                                ? 'bg-green-500'
                                : item.qc_snapshot.qc_score >= 0.6
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${item.qc_snapshot.qc_score * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium min-w-[3ch]">
                          {Math.round(item.qc_snapshot.qc_score * 100)}
                        </span>
                      </div>
                    </div>
                    <div className="col-span-2">
                      <span className="text-sm">{item.qc_snapshot.word_count} words</span>
                    </div>
                    <div className="col-span-2">
                      <Badge variant={item.qc_snapshot.issues_found > 0 ? 'destructive' : 'secondary'}>
                        {item.qc_snapshot.issues_found} issues
                      </Badge>
                    </div>
                    <div className="col-span-2 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onViewItem(item)}
                      >
                        <Eye className="h-3 w-3 mr-1" />
                        View
                      </Button>
                      {item.review_status === 'pending' || item.review_status === 'regenerated' ? (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-green-600 hover:text-green-700"
                            onClick={() => onApprove(item.id)}
                          >
                            <CheckCircle2 className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => onReject(item.id)}
                          >
                            <XCircle className="h-3 w-3" />
                          </Button>
                        </>
                      ) : null}
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t pt-4 mt-2">
                    <div className="space-y-4">
                      {/* Article Preview */}
                      <div>
                        <h4 className="text-sm font-medium mb-2">Article Preview</h4>
                        <div className="bg-muted p-4 rounded-lg max-h-60 overflow-y-auto">
                          <pre className="text-sm whitespace-pre-wrap font-sans">
                            {item.qc_snapshot.article_text.slice(0, 500)}
                            {item.qc_snapshot.article_text.length > 500 && '...'}
                          </pre>
                        </div>
                      </div>

                      {/* QC Details */}
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">QC Status</p>
                          <Badge variant="outline">{item.qc_snapshot.qc_status}</Badge>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Regenerations</p>
                          <p className="text-sm font-medium">{item.regeneration_count}</p>
                        </div>
                        {item.reviewer_notes && (
                          <div className="col-span-3">
                            <p className="text-sm text-muted-foreground">Reviewer Notes</p>
                            <p className="text-sm">{item.reviewer_notes}</p>
                          </div>
                        )}
                      </div>

                      {/* Quick Actions */}
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onViewItem(item)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Full Article
                        </Button>
                        {(item.review_status === 'pending' || item.review_status === 'regenerated') && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-green-600"
                              onClick={() => onApprove(item.id)}
                            >
                              <CheckCircle2 className="h-4 w-4 mr-2" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600"
                              onClick={() => onReject(item.id)}
                            >
                              <XCircle className="h-4 w-4 mr-2" />
                              Reject
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-orange-600"
                              onClick={() => {
                                const notes = prompt('Enter regeneration notes:')
                                if (notes) {
                                  onRequestRegeneration(item.id, notes)
                                }
                              }}
                            >
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Request Regeneration
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })
      )}
    </div>
  )
}
