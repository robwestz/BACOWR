'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ArrowRight, ArrowLeft, Sparkles, Settings2, Target, FileCheck } from 'lucide-react'
import { useCreateJobWizard, useJobsStore, useToastStore } from '@/lib/store'
import { jobsAPI } from '@/lib/api/client'
import { formatCurrency } from '@/lib/utils/format'

const steps = [
  { id: 0, name: 'Input', icon: Target, description: 'Basic job information' },
  { id: 1, name: 'Provider', icon: Settings2, description: 'Choose LLM provider' },
  { id: 2, name: 'Strategy', icon: Sparkles, description: 'Writing strategy' },
  { id: 3, name: 'Review', icon: FileCheck, description: 'Review and submit' },
]

const providers = [
  { id: 'auto', name: 'Auto', description: 'Automatic provider selection', cost: '$0.10-0.30' },
  { id: 'anthropic', name: 'Claude', description: 'Best for Swedish content', cost: '$0.15-0.25' },
  { id: 'openai', name: 'GPT', description: 'Fast and versatile', cost: '$0.10-0.20' },
  { id: 'google', name: 'Gemini', description: 'Cost-effective option', cost: '$0.05-0.15' },
]

const strategies = [
  {
    id: 'multi_stage',
    name: 'Multi-Stage',
    description: '3-stage generation for best quality',
    cost: 'Higher',
    quality: 5,
    speed: 3,
  },
  {
    id: 'single_shot',
    name: 'Single-Shot',
    description: 'One LLM call for faster results',
    cost: 'Lower',
    quality: 4,
    speed: 5,
  },
]

export default function NewJobPage() {
  const router = useRouter()
  const { step, input, setStep, updateInput, reset } = useCreateJobWizard()
  const addJob = useJobsStore((state) => state.addJob)
  const addToast = useToastStore((state) => state.addToast)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const progress = ((step + 1) / steps.length) * 100

  const handleNext = () => {
    if (step < steps.length - 1) {
      setStep(step + 1)
    }
  }

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1)
    }
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)

    try {
      const job = await jobsAPI.create({
        publisher_domain: input.publisher_domain,
        target_url: input.target_url,
        anchor_text: input.anchor_text,
        llm_provider: input.llm_provider as any,
        writing_strategy: input.strategy as any, // Backend expects writing_strategy
        country: input.country,
      })

      addJob(job)
      addToast({
        type: 'success',
        title: 'Job Created',
        message: 'Your article is being generated!',
      })

      reset()
      router.push(`/jobs/${job.job_meta.job_id}`)
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Failed to Create Job',
        message: error instanceof Error ? error.message : 'Unknown error',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const canProceed = () => {
    if (step === 0) {
      return input.publisher_domain && input.target_url && input.anchor_text
    }
    return true
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Create New Job</h1>
        <p className="text-muted-foreground mt-1">
          Generate a high-quality backlink article in 4 simple steps
        </p>
      </div>

      {/* Progress */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              {steps.map((s, i) => (
                <React.Fragment key={s.id}>
                  <div className="flex items-center gap-2">
                    <div
                      className={`h-10 w-10 rounded-full flex items-center justify-center ${
                        i <= step
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      <s.icon className="h-5 w-5" />
                    </div>
                    <div className="hidden md:block">
                      <p className="font-medium">{s.name}</p>
                      <p className="text-xs text-muted-foreground">{s.description}</p>
                    </div>
                  </div>
                  {i < steps.length - 1 && (
                    <div className="flex-1 h-0.5 bg-muted mx-4" />
                  )}
                </React.Fragment>
              ))}
            </div>
            <Progress value={progress} />
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>{steps[step].name}</CardTitle>
          <CardDescription>{steps[step].description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Step 0: Input */}
          {step === 0 && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Publisher Domain *
                </label>
                <Input
                  placeholder="example.com"
                  value={input.publisher_domain}
                  onChange={(e) =>
                    updateInput({ publisher_domain: e.target.value })
                  }
                />
                <p className="text-xs text-muted-foreground mt-1">
                  The domain where the article will be published
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Target URL *
                </label>
                <Input
                  type="url"
                  placeholder="https://client.com/product"
                  value={input.target_url}
                  onChange={(e) => updateInput({ target_url: e.target.value })}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  The URL you want to link to
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Anchor Text *
                </label>
                <Input
                  placeholder="best solution for..."
                  value={input.anchor_text}
                  onChange={(e) => updateInput({ anchor_text: e.target.value })}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  The clickable text for the link
                </p>
              </div>
            </div>
          )}

          {/* Step 1: Provider */}
          {step === 1 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {providers.map((provider) => (
                <Card
                  key={provider.id}
                  className={`cursor-pointer transition-all ${
                    input.llm_provider === provider.id
                      ? 'border-primary bg-primary/5'
                      : 'hover:border-primary/50'
                  }`}
                  onClick={() => updateInput({ llm_provider: provider.id })}
                >
                  <CardContent className="pt-6">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold">{provider.name}</h3>
                        <Badge variant="secondary">{provider.cost}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {provider.description}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Step 2: Strategy */}
          {step === 2 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {strategies.map((strategy) => (
                <Card
                  key={strategy.id}
                  className={`cursor-pointer transition-all ${
                    input.strategy === strategy.id
                      ? 'border-primary bg-primary/5'
                      : 'hover:border-primary/50'
                  }`}
                  onClick={() => updateInput({ strategy: strategy.id })}
                >
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold">{strategy.name}</h3>
                        <Badge variant="secondary">{strategy.cost} Cost</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {strategy.description}
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span>Quality</span>
                          <div className="flex gap-0.5">
                            {Array.from({ length: 5 }).map((_, i) => (
                              <div
                                key={i}
                                className={`h-2 w-2 rounded-full ${
                                  i < strategy.quality
                                    ? 'bg-primary'
                                    : 'bg-muted'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span>Speed</span>
                          <div className="flex gap-0.5">
                            {Array.from({ length: 5 }).map((_, i) => (
                              <div
                                key={i}
                                className={`h-2 w-2 rounded-full ${
                                  i < strategy.speed ? 'bg-primary' : 'bg-muted'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="rounded-lg border p-4 space-y-3">
                <h3 className="font-semibold">Job Summary</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground">Publisher</p>
                    <p className="font-medium">{input.publisher_domain}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Target</p>
                    <p className="font-medium truncate">{input.target_url}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Anchor</p>
                    <p className="font-medium">{input.anchor_text}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Provider</p>
                    <p className="font-medium capitalize">{input.llm_provider}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Strategy</p>
                    <p className="font-medium capitalize">
                      {input.strategy.replace('_', ' ')}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Country</p>
                    <p className="font-medium uppercase">{input.country}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-primary/5 border border-primary/20 p-4">
                <h3 className="font-semibold mb-2">Cost Estimate</h3>
                <p className="text-2xl font-bold">{formatCurrency(0.15)}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Estimated cost for this job (may vary)
                </p>
              </div>

              <div className="rounded-lg bg-muted p-4">
                <p className="text-sm">
                  <strong>Next:</strong> Job will be queued and processed. You'll
                  receive real-time updates via WebSocket. Expected completion:
                  30-60 seconds.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={step === 0 || isSubmitting}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        {step < steps.length - 1 ? (
          <Button onClick={handleNext} disabled={!canProceed()}>
            Next
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={!canProceed() || isSubmitting}
            isLoading={isSubmitting}
          >
            Create Job
            <Sparkles className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>
    </div>
  )
}
