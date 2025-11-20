'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Zap, ArrowRight, Sparkles } from 'lucide-react'
import { jobsAPI } from '@/lib/api/client'
import { useJobsStore, useToastStore } from '@/lib/store'
import type { JobInput } from '@/types'

export function QuickStartWidget() {
  const router = useRouter()
  const addJob = useJobsStore((state) => state.addJob)
  const addToast = useToastStore((state) => state.addToast)

  const [input, setInput] = useState<JobInput>({
    publisher_domain: '',
    target_url: '',
    anchor_text: '',
  })
  const [isLoading, setIsLoading] = useState(false)

  const isValid =
    input.publisher_domain && input.target_url && input.anchor_text

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) return

    setIsLoading(true)

    try {
      const job = await jobsAPI.create({
        ...input,
        llm_provider: 'auto',
        strategy: 'multi_stage',
      })

      addJob(job)
      addToast({
        type: 'success',
        title: 'Job Created',
        message: 'Your article is being generated!',
      })

      // Navigate to job details
      router.push(`/jobs/${job.job_meta.job_id}`)
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Failed to Create Job',
        message: error instanceof Error ? error.message : 'Unknown error',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            <CardTitle>Quick Start</CardTitle>
          </div>
          <Badge variant="secondary" className="gap-1">
            <Sparkles className="h-3 w-3" />
            0-60 seconds
          </Badge>
        </div>
        <CardDescription>
          Create your first article in under a minute
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              Publisher Domain
            </label>
            <Input
              placeholder="example.com"
              value={input.publisher_domain}
              onChange={(e) =>
                setInput({ ...input, publisher_domain: e.target.value })
              }
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">
              Target URL
            </label>
            <Input
              type="url"
              placeholder="https://client.com/product"
              value={input.target_url}
              onChange={(e) =>
                setInput({ ...input, target_url: e.target.value })
              }
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">
              Anchor Text
            </label>
            <Input
              placeholder="best solution for..."
              value={input.anchor_text}
              onChange={(e) =>
                setInput({ ...input, anchor_text: e.target.value })
              }
              disabled={isLoading}
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={!isValid || isLoading}
            isLoading={isLoading}
          >
            Generate Article
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>

          <p className="text-xs text-center text-muted-foreground">
            Using Claude Sonnet • Multi-stage strategy • ~30-60 seconds
          </p>
        </form>
      </CardContent>
    </Card>
  )
}
