import React from 'react'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-muted rounded ${className}`}
      role="status"
      aria-label="Loading"
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-6 w-24" />
      </div>
      <Skeleton className="h-4 w-full" />
      <div className="grid grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <div key={i}>
            <Skeleton className="h-3 w-16 mb-2" />
            <Skeleton className="h-5 w-12" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-3 bg-muted/50 rounded-t-lg">
        <Skeleton className="h-4 w-4" />
        <div className="grid grid-cols-12 gap-4 flex-1">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-24 col-span-3" />
          <Skeleton className="h-4 w-20 col-span-2" />
          <Skeleton className="h-4 w-20 col-span-2" />
          <Skeleton className="h-4 w-16 col-span-2" />
          <Skeleton className="h-4 w-20 col-span-2" />
        </div>
      </div>

      {/* Rows */}
      {[...Array(rows)].map((_, i) => (
        <div key={i} className="border rounded-lg p-4">
          <div className="flex items-center gap-4">
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-4" />
            <div className="grid grid-cols-12 gap-4 flex-1">
              <Skeleton className="h-6 w-20" />
              <Skeleton className="h-6 w-32 col-span-3" />
              <Skeleton className="h-6 w-24 col-span-2" />
              <Skeleton className="h-6 w-20 col-span-2" />
              <Skeleton className="h-6 w-16 col-span-2" />
              <div className="col-span-2 flex gap-2">
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-8 w-8" />
                <Skeleton className="h-8 w-8" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-16" />
            </div>
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  )
}
