'use client'

import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Search, Filter, X } from 'lucide-react'
import type { ReviewItemStatus } from '@/types'

interface BatchFiltersProps {
  statusFilter: ReviewItemStatus | 'all'
  onStatusFilterChange: (status: ReviewItemStatus | 'all') => void
  searchQuery: string
  onSearchChange: (query: string) => void
  showQCFilters?: boolean
  qcScoreMin?: number
  qcScoreMax?: number
  onQCScoreChange?: (min: number, max: number) => void
}

const STATUS_OPTIONS: Array<{ value: ReviewItemStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'needs_regeneration', label: 'Needs Regen' },
  { value: 'regenerating', label: 'Regenerating' },
  { value: 'regenerated', label: 'Regenerated' },
]

export function BatchFilters({
  statusFilter,
  onStatusFilterChange,
  searchQuery,
  onSearchChange,
  showQCFilters = false,
  qcScoreMin = 0,
  qcScoreMax = 100,
  onQCScoreChange,
}: BatchFiltersProps) {
  const hasActiveFilters = statusFilter !== 'all' || searchQuery !== ''

  const clearFilters = () => {
    onStatusFilterChange('all')
    onSearchChange('')
    if (onQCScoreChange) {
      onQCScoreChange(0, 100)
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Search */}
          <div>
            <Label htmlFor="search" className="text-sm font-medium mb-2 block">
              Search
            </Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="search"
                placeholder="Search by job ID..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label className="text-sm font-medium">
                <Filter className="inline h-4 w-4 mr-1" />
                Status
              </Label>
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="h-auto py-1 px-2 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  variant={statusFilter === option.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onStatusFilterChange(option.value)}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>

          {/* QC Score Filter */}
          {showQCFilters && onQCScoreChange && (
            <div>
              <Label className="text-sm font-medium mb-2 block">
                QC Score Range
              </Label>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={qcScoreMin}
                    onChange={(e) => onQCScoreChange(parseInt(e.target.value), qcScoreMax)}
                    placeholder="Min"
                  />
                </div>
                <span className="text-muted-foreground">to</span>
                <div className="flex-1">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={qcScoreMax}
                    onChange={(e) => onQCScoreChange(qcScoreMin, parseInt(e.target.value))}
                    placeholder="Max"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
