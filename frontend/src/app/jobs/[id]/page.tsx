'use client'

import React, { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { JobProgressBar } from '@/components/jobs/JobProgressBar'
import { QCBadge } from '@/components/jobs/QCBadge'
import { jobsAPI } from '@/lib/api/client'
import { useWebSocket } from '@/lib/api/websocket'
import { formatRelativeTime, formatCurrency, formatDuration } from '@/lib/utils/format'
import {
  Download,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Clock,
  DollarSign,
} from 'lucide-react'

export default function JobDetailsPage() {
  const params = useParams()
  const jobId = params.id as string
  const { subscribeToJob, unsubscribeFromJob } = useWebSocket()

  const { data: job, refetch } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsAPI.get(jobId),
  })

  useEffect(() => {
    if (jobId) {
      subscribeToJob(jobId)
      return () => unsubscribeFromJob(jobId)
    }
  }, [jobId, subscribeToJob, unsubscribeFromJob])

  if (!job) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    )
  }

  const { job_meta, input_minimal, qc_report, metrics, article } = job

  const handleExport = async (format: 'md' | 'pdf' | 'html') => {
    const blob = await jobsAPI.export(jobId, format)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${jobId}.${format}`
    a.click()
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{input_minimal.publisher_domain}</h1>
          <p className="text-muted-foreground mt-1">
            {formatRelativeTime(job_meta.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => handleExport('md')}>
            <Download className="h-4 w-4 mr-2" />
            MD
          </Button>
          <Button variant="outline" onClick={() => handleExport('pdf')}>
            <Download className="h-4 w-4 mr-2" />
            PDF
          </Button>
          <Button variant="outline" onClick={() => handleExport('html')}>
            <Download className="h-4 w-4 mr-2" />
            HTML
          </Button>
        </div>
      </div>

      {/* Status Bar */}
      {job_meta.status === 'RUNNING' && (
        <JobProgressBar
          jobId={jobId}
          status={job_meta.status}
          progress={50}
          message="Generating article..."
        />
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge variant={job_meta.status === 'DELIVERED' ? 'success' : 'secondary'}>
                  {job_meta.status}
                </Badge>
              </div>
              <CheckCircle2 className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Duration</p>
                <p className="text-lg font-bold">
                  {formatDuration(metrics?.generation?.duration_seconds || 0)}
                </p>
              </div>
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Cost</p>
                <p className="text-lg font-bold">
                  {formatCurrency(metrics?.generation?.cost_usd || 0)}
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
                <p className="text-sm text-muted-foreground">QC Status</p>
                {qc_report && (
                  <QCBadge status={qc_report.status} showIcon={false} />
                )}
              </div>
              <AlertTriangle className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="article" className="space-y-4">
        <TabsList>
          <TabsTrigger value="article">Article</TabsTrigger>
          <TabsTrigger value="qc">QC Report</TabsTrigger>
          <TabsTrigger value="details">Job Details</TabsTrigger>
          <TabsTrigger value="execution">Execution Log</TabsTrigger>
        </TabsList>

        {/* Article Tab */}
        <TabsContent value="article">
          <Card>
            <CardHeader>
              <CardTitle>Generated Article</CardTitle>
              <CardDescription>
                {article?.split(' ').length || 0} words
              </CardDescription>
            </CardHeader>
            <CardContent>
              {article ? (
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown>{article}</ReactMarkdown>
                </div>
              ) : (
                <p className="text-muted-foreground">Article not yet generated</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* QC Report Tab */}
        <TabsContent value="qc">
          <Card>
            <CardHeader>
              <CardTitle>Quality Control Report</CardTitle>
              <CardDescription>
                Overall Score: {qc_report?.overall_score || 0}/100
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {qc_report && (
                <>
                  <div className="flex items-center gap-4">
                    <QCBadge status={qc_report.status} score={qc_report.overall_score} />
                    {qc_report.human_signoff_required && (
                      <Badge variant="warning">Human Signoff Required</Badge>
                    )}
                  </div>

                  {/* Issues */}
                  {qc_report.issues.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-2">Issues Found</h3>
                      <div className="space-y-2">
                        {qc_report.issues.map((issue, i) => (
                          <div
                            key={i}
                            className="p-3 rounded-lg border bg-card"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <Badge variant="outline">{issue.category}</Badge>
                                  <Badge
                                    variant={
                                      issue.severity === 'high'
                                        ? 'destructive'
                                        : issue.severity === 'medium'
                                        ? 'warning'
                                        : 'secondary'
                                    }
                                  >
                                    {issue.severity}
                                  </Badge>
                                  {issue.fixed && (
                                    <Badge variant="success">Fixed</Badge>
                                  )}
                                </div>
                                <p className="text-sm">{issue.description}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* AutoFix Logs */}
                  {qc_report.autofix_logs.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-2">AutoFix Actions</h3>
                      <div className="space-y-2">
                        {qc_report.autofix_logs.map((log, i) => (
                          <div
                            key={i}
                            className="p-3 rounded-lg bg-muted text-sm font-mono"
                          >
                            <p className="font-bold">{log.action}</p>
                            <div className="mt-2 space-y-1">
                              <p>
                                <span className="text-red-500">- {log.before}</span>
                              </p>
                              <p>
                                <span className="text-green-500">+ {log.after}</span>
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Job Details Tab */}
        <TabsContent value="details">
          <Card>
            <CardHeader>
              <CardTitle>Job Package</CardTitle>
              <CardDescription>Complete job specification</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Input */}
                <div>
                  <h3 className="font-semibold mb-2">Input</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground w-24">Publisher:</span>
                      <span className="font-medium">{input_minimal.publisher_domain}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground w-24">Target:</span>
                      <a
                        href={input_minimal.target_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline flex items-center gap-1"
                      >
                        {input_minimal.target_url}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground w-24">Anchor:</span>
                      <span className="font-medium">{input_minimal.anchor_text}</span>
                    </div>
                  </div>
                </div>

                {/* Profiles */}
                <div>
                  <h3 className="font-semibold mb-2">Profiles</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg border">
                      <p className="font-medium mb-2">Publisher Profile</p>
                      <div className="text-sm space-y-1">
                        <p>Tone: {job.publisher_profile?.tone}</p>
                        <p>Language: {job.publisher_profile?.language}</p>
                      </div>
                    </div>
                    <div className="p-3 rounded-lg border">
                      <p className="font-medium mb-2">Target Profile</p>
                      <div className="text-sm space-y-1">
                        <p>Intent: {job.target_profile?.intent}</p>
                        <p>Language: {job.target_profile?.language}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Full JSON */}
                <details>
                  <summary className="cursor-pointer font-semibold mb-2">
                    Full Job Package (JSON)
                  </summary>
                  <pre className="p-4 rounded-lg bg-muted overflow-auto text-xs">
                    {JSON.stringify(job, null, 2)}
                  </pre>
                </details>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Execution Log Tab */}
        <TabsContent value="execution">
          <Card>
            <CardHeader>
              <CardTitle>Execution Log</CardTitle>
              <CardDescription>Step-by-step execution trace</CardDescription>
            </CardHeader>
            <CardContent>
              {job.execution_log ? (
                <div className="space-y-2">
                  {job.execution_log.log_entries.map((entry, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 p-2 rounded text-sm font-mono"
                    >
                      <span className="text-muted-foreground whitespace-nowrap">
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </span>
                      <span className="flex-1">
                        {entry.type === 'state_transition' ? (
                          <>
                            {entry.from_state} → {entry.to_state}
                          </>
                        ) : (
                          entry.message
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No execution log available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
