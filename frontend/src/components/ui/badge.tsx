import * as React from 'react'
import { cn } from '@/lib/utils/cn'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'
  size?: 'default' | 'sm' | 'lg'
}

function Badge({ className, variant = 'default', size = 'default', ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full border font-semibold transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        {
          'border-transparent bg-primary text-primary-foreground hover:bg-primary/80':
            variant === 'default',
          'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80':
            variant === 'secondary',
          'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80':
            variant === 'destructive',
          'text-foreground': variant === 'outline',
          'border-transparent bg-green-500 text-white hover:bg-green-600':
            variant === 'success',
          'border-transparent bg-yellow-500 text-white hover:bg-yellow-600':
            variant === 'warning',
          'px-2.5 py-0.5 text-xs': size === 'default',
          'px-2 py-0.5 text-[10px]': size === 'sm',
          'px-3 py-1 text-sm': size === 'lg',
        },
        className
      )}
      {...props}
    />
  )
}

export { Badge }
