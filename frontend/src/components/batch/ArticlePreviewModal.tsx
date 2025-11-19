'use client'

import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { CheckCircle2, XCircle, RefreshCw, Download, Copy } from 'lucide-react'
import type { BatchReviewItem } from '@/types'

interface ArticlePreviewModalProps {
  item: BatchReviewItem | null
  isOpen: boolean
  onClose: () => void
  onApprove?: (itemId: string) => void
  onReject?: (itemId: string) => void
  onRequestRegeneration?: (itemId: string, notes: string) => void
}

export function ArticlePreviewModal({
  item,
  isOpen,
  onClose,
  onApprove,
  onReject,
  onRequestRegeneration,
}: ArticlePreviewModalProps) {
  if (!item) return null

  const handleCopyArticle = () => {
    navigator.clipboard.writeText(item.qc_snapshot.article_text)
    // Could add toast notification here
  }

  const handleDownload = () => {
    const blob = new Blob([item.qc_snapshot.article_text], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `article-${item.job_id}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const canReview = item.review_status === 'pending' || item.review_status === 'regenerated'

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            Article Preview
            <Badge variant="outline">{item.review_status}</Badge>
          </DialogTitle>
          <DialogDescription>
            Job ID: <code className="text-xs">{item.job_id}</code>
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="article" className="flex-1 overflow-hidden flex flex-col">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="article">Article</TabsTrigger>
            <TabsTrigger value="qc">QC Report</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
          </TabsList>

          <TabsContent value="article" className="flex-1 overflow-auto mt-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCopyArticle}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleDownload}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  {item.qc_snapshot.word_count} words
                </p>
              </div>

              <div className="bg-muted p-6 rounded-lg">
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                  {item.qc_snapshot.article_text}
                </pre>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="qc" className="flex-1 overflow-auto mt-4">
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">QC Score</p>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 rounded-full bg-background overflow-hidden">
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
                    <p className="text-2xl font-bold">
                      {Math.round(item.qc_snapshot.qc_score * 100)}
                    </p>
                  </div>
                </div>

                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">QC Status</p>
                  <Badge variant="outline" className="mt-1">
                    {item.qc_snapshot.qc_status}
                  </Badge>
                </div>

                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Issues Found</p>
                  <p className="text-2xl font-bold">
                    {item.qc_snapshot.issues_found}
                  </p>
                </div>
              </div>

              {item.reviewer_notes && (
                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-2">Reviewer Notes</p>
                  <p className="text-sm">{item.reviewer_notes}</p>
                </div>
              )}

              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm text-muted-foreground mb-2">Regeneration History</p>
                <p className="text-sm">
                  This article has been regenerated{' '}
                  <strong>{item.regeneration_count}</strong> time
                  {item.regeneration_count !== 1 ? 's' : ''}.
                </p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="metadata" className="flex-1 overflow-auto mt-4">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Item ID</p>
                  <code className="text-xs">{item.id}</code>
                </div>

                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Job ID</p>
                  <code className="text-xs">{item.job_id}</code>
                </div>

                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Batch ID</p>
                  <code className="text-xs">{item.batch_id}</code>
                </div>

                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Review Status</p>
                  <Badge>{item.review_status}</Badge>
                </div>

                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Created At</p>
                  <p className="text-sm">{new Date(item.created_at).toLocaleString()}</p>
                </div>

                {item.reviewed_at && (
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground mb-1">Reviewed At</p>
                    <p className="text-sm">{new Date(item.reviewed_at).toLocaleString()}</p>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-4">
          {canReview && onApprove && onReject && onRequestRegeneration && (
            <div className="flex gap-2 w-full">
              <Button
                variant="outline"
                className="flex-1 text-green-600 hover:text-green-700"
                onClick={() => {
                  onApprove(item.id)
                  onClose()
                }}
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Approve
              </Button>
              <Button
                variant="outline"
                className="flex-1 text-red-600 hover:text-red-700"
                onClick={() => {
                  onReject(item.id)
                  onClose()
                }}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
              <Button
                variant="outline"
                className="flex-1 text-orange-600 hover:text-orange-700"
                onClick={() => {
                  const notes = prompt('Enter regeneration notes:')
                  if (notes) {
                    onRequestRegeneration(item.id, notes)
                    onClose()
                  }
                }}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Regenerate
              </Button>
            </div>
          )}
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
