'use client'

import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  CheckCircle2,
  XCircle,
  Download,
  Trash2,
  RefreshCw,
} from 'lucide-react'

interface BulkActionsProps {
  selectedCount: number
  onBulkApprove: () => void
  onBulkReject: () => void
  onBulkExport: () => void
  onClearSelection: () => void
  isLoading?: boolean
}

export function BulkActions({
  selectedCount,
  onBulkApprove,
  onBulkReject,
  onBulkExport,
  onClearSelection,
  isLoading = false,
}: BulkActionsProps) {
  if (selectedCount === 0) {
    return null
  }

  return (
    <Card className="border-primary">
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <p className="text-sm font-medium">
              {selectedCount} item{selectedCount !== 1 ? 's' : ''} selected
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearSelection}
              disabled={isLoading}
            >
              Clear Selection
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={onBulkApprove}
              disabled={isLoading}
              className="text-green-600 hover:text-green-700"
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Approve Selected
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onBulkReject}
              disabled={isLoading}
              className="text-red-600 hover:text-red-700"
            >
              <XCircle className="h-4 w-4 mr-2" />
              Reject Selected
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onBulkExport}
              disabled={isLoading}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Selected
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
