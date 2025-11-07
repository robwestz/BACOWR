'use client'

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { backlinksAPI } from '@/lib/api/client'
import { formatRelativeTime, formatCurrency } from '@/lib/utils/format'
import { Search, Link as LinkIcon, ExternalLink, TrendingUp, DollarSign, Target } from 'lucide-react'
import Link from 'next/link'

export default function BacklinksPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)

  const { data: backlinks, isLoading } = useQuery({
    queryKey: ['backlinks', page, searchQuery],
    queryFn: () =>
      backlinksAPI.list({
        page,
        per_page: 20,
        search: searchQuery || undefined,
      }),
  })

  const { data: analytics } = useQuery({
    queryKey: ['backlinks-analytics'],
    queryFn: () => backlinksAPI.analytics(),
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
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Backlinks Library</h1>
        <p className="text-muted-foreground mt-1">
          Browse and analyze your 3000+ historical backlinks
        </p>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Backlinks</p>
                  <p className="text-2xl font-bold">{analytics.total}</p>
                </div>
                <LinkIcon className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Delivered</p>
                  <p className="text-2xl font-bold">
                    {analytics.by_status?.DELIVERED || 0}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Cost</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(analytics.total_cost)}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg QC Score</p>
                  <p className="text-2xl font-bold">
                    {analytics.avg_qc_score?.toFixed(0) || 0}
                  </p>
                </div>
                <Target className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by publisher, target, or anchor..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button variant="outline">Filter</Button>
          </div>
        </CardContent>
      </Card>

      {/* Backlinks List */}
      <div className="space-y-3">
        {backlinks?.backlinks.map((backlink) => (
          <Card
            key={backlink.id}
            className="hover:shadow-md transition-shadow cursor-pointer"
          >
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-lg">
                      {backlink.publisher}
                    </h3>
                    <Badge
                      variant={
                        backlink.status === 'DELIVERED'
                          ? 'success'
                          : 'secondary'
                      }
                    >
                      {backlink.status}
                    </Badge>
                    {backlink.qc_score && (
                      <Badge variant="outline">QC: {backlink.qc_score}/100</Badge>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-sm">
                    <ExternalLink className="h-4 w-4 text-muted-foreground" />
                    <a
                      href={backlink.target}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline truncate"
                    >
                      {backlink.target}
                    </a>
                  </div>

                  <p className="text-sm text-muted-foreground">
                    <strong>Anchor:</strong> {backlink.anchor}
                  </p>

                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>{formatRelativeTime(backlink.created_at)}</span>
                    {backlink.cost_usd && (
                      <span>{formatCurrency(backlink.cost_usd)}</span>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/jobs/${backlink.id}`}>View</Link>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => backlinksAPI.generateSimilar(backlink.id)}
                  >
                    Generate Similar
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pagination */}
      {backlinks && backlinks.total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {Math.ceil(backlinks.total / 20)}
          </span>
          <Button
            variant="outline"
            disabled={page >= Math.ceil(backlinks.total / 20)}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
