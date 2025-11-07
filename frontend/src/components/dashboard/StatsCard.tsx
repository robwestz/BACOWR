import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { ArrowUpIcon, ArrowDownIcon } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

interface StatsCardProps {
  title: string
  value: string | number
  icon?: React.ReactNode
  trend?: {
    value: number
    label: string
  }
  className?: string
}

export function StatsCard({ title, value, icon, trend, className }: StatsCardProps) {
  const isPositive = trend && trend.value > 0
  const isNegative = trend && trend.value < 0

  return (
    <Card className={cn('hover:shadow-md transition-shadow', className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {trend && (
              <div className="flex items-center gap-1 text-xs">
                {isPositive && (
                  <ArrowUpIcon className="h-3 w-3 text-green-500" />
                )}
                {isNegative && (
                  <ArrowDownIcon className="h-3 w-3 text-red-500" />
                )}
                <span
                  className={cn({
                    'text-green-500': isPositive,
                    'text-red-500': isNegative,
                    'text-muted-foreground': !isPositive && !isNegative,
                  })}
                >
                  {Math.abs(trend.value)}% {trend.label}
                </span>
              </div>
            )}
          </div>
          {icon && (
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              {icon}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
