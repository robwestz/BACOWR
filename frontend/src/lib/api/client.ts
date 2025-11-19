import type {
  ApiResponse,
  JobInput,
  JobPackage,
  JobListResponse,
  BacklinkRecord,
  BatchJob,
  BatchReview,
  BatchReviewListResponse,
  BatchReviewItem,
  BatchReviewItemsResponse,
  ReviewDecision,
  BatchExportResponse,
  UserSettings,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new APIError(
        response.status,
        error.message || `HTTP ${response.status}`,
        error.details
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof APIError) throw error
    throw new APIError(0, `Network error: ${error}`)
  }
}

// Jobs API
export const jobsAPI = {
  // Create new job
  create: async (input: JobInput): Promise<JobPackage> => {
    return fetchAPI<JobPackage>('/api/jobs', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },

  // Get job by ID
  get: async (jobId: string): Promise<JobPackage> => {
    return fetchAPI<JobPackage>(`/api/jobs/${jobId}`)
  },

  // List jobs with pagination and filters
  list: async (params?: {
    page?: number
    per_page?: number
    status?: string[]
    search?: string
  }): Promise<JobListResponse> => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set('page', params.page.toString())
    if (params?.per_page) searchParams.set('per_page', params.per_page.toString())
    if (params?.status) searchParams.set('status', params.status.join(','))
    if (params?.search) searchParams.set('search', params.search)

    const query = searchParams.toString()
    return fetchAPI<JobListResponse>(`/api/jobs${query ? `?${query}` : ''}`)
  },

  // Delete job
  delete: async (jobId: string): Promise<void> => {
    return fetchAPI<void>(`/api/jobs/${jobId}`, {
      method: 'DELETE',
    })
  },

  // Get job article
  getArticle: async (jobId: string): Promise<string> => {
    return fetchAPI<string>(`/api/jobs/${jobId}/article`)
  },

  // Get job QC report
  getQCReport: async (jobId: string): Promise<any> => {
    return fetchAPI<any>(`/api/jobs/${jobId}/qc-report`)
  },

  // Get job execution log
  getExecutionLog: async (jobId: string): Promise<any> => {
    return fetchAPI<any>(`/api/jobs/${jobId}/execution-log`)
  },

  // Export job (MD, PDF, HTML)
  export: async (jobId: string, format: 'md' | 'pdf' | 'html'): Promise<Blob> => {
    const response = await fetch(`${API_URL}/api/jobs/${jobId}/export?format=${format}`)
    if (!response.ok) throw new Error('Export failed')
    return response.blob()
  },
}

// Batch API
export const batchAPI = {
  // Create batch job
  create: async (jobs: JobInput[]): Promise<BatchJob> => {
    return fetchAPI<BatchJob>('/api/batch', {
      method: 'POST',
      body: JSON.stringify({ jobs }),
    })
  },

  // Get batch status
  get: async (batchId: string): Promise<BatchJob> => {
    return fetchAPI<BatchJob>(`/api/batch/${batchId}`)
  },

  // List batches
  list: async (): Promise<BatchJob[]> => {
    return fetchAPI<BatchJob[]>('/api/batch')
  },

  // Cancel batch
  cancel: async (batchId: string): Promise<void> => {
    return fetchAPI<void>(`/api/batch/${batchId}/cancel`, {
      method: 'POST',
    })
  },
}

// Batch Review API (Day 2 QA Workflow)
export const batchReviewAPI = {
  // Create batch from completed jobs
  create: async (data: {
    name: string
    description?: string
    job_ids: string[]
    batch_config?: Record<string, any>
  }): Promise<BatchReview> => {
    return fetchAPI<BatchReview>('/api/v1/batches', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  // List all batches with pagination
  list: async (params?: {
    page?: number
    per_page?: number
    status?: string
  }): Promise<BatchReviewListResponse> => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set('page', params.page.toString())
    if (params?.per_page) searchParams.set('per_page', params.per_page.toString())
    if (params?.status) searchParams.set('status', params.status)

    const query = searchParams.toString()
    return fetchAPI<BatchReviewListResponse>(
      `/api/v1/batches${query ? `?${query}` : ''}`
    )
  },

  // Get batch by ID
  get: async (batchId: string): Promise<BatchReview> => {
    return fetchAPI<BatchReview>(`/api/v1/batches/${batchId}`)
  },

  // Get batch items
  getItems: async (batchId: string, params?: {
    status?: string
    limit?: number
    offset?: number
  }): Promise<BatchReviewItemsResponse> => {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())

    const query = searchParams.toString()
    return fetchAPI<BatchReviewItemsResponse>(
      `/api/v1/batches/${batchId}/items${query ? `?${query}` : ''}`
    )
  },

  // Review an item (approve/reject/regenerate)
  reviewItem: async (
    batchId: string,
    itemId: string,
    decision: ReviewDecision
  ): Promise<{ message: string; item: BatchReviewItem }> => {
    return fetchAPI(`/api/v1/batches/${batchId}/items/${itemId}/review`, {
      method: 'POST',
      body: JSON.stringify(decision),
    })
  },

  // Regenerate item content
  regenerateItem: async (
    batchId: string,
    itemId: string
  ): Promise<{ message: string; job_id: string }> => {
    return fetchAPI(`/api/v1/batches/${batchId}/items/${itemId}/regenerate`, {
      method: 'POST',
    })
  },

  // Export approved batch
  exportBatch: async (
    batchId: string,
    format: string = 'json'
  ): Promise<BatchExportResponse> => {
    return fetchAPI<BatchExportResponse>(`/api/v1/batches/${batchId}/export`, {
      method: 'POST',
      body: JSON.stringify({ export_format: format }),
    })
  },

  // Get batch statistics
  getStats: async (
    batchId: string
  ): Promise<{
    batch_id: string
    total_items: number
    review_progress: {
      pending: number
      approved: number
      rejected: number
      needs_regeneration: number
    }
    quality_metrics: {
      average_qc_score: number
      approval_rate: number
    }
  }> => {
    return fetchAPI(`/api/v1/batches/${batchId}/stats`)
  },

  // Delete batch
  delete: async (batchId: string): Promise<void> => {
    return fetchAPI<void>(`/api/v1/batches/${batchId}`, {
      method: 'DELETE',
    })
  },
}

// Backlinks API
export const backlinksAPI = {
  // List backlinks
  list: async (params?: {
    page?: number
    per_page?: number
    search?: string
    status?: string[]
  }): Promise<{
    backlinks: BacklinkRecord[]
    total: number
  }> => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set('page', params.page.toString())
    if (params?.per_page) searchParams.set('per_page', params.per_page.toString())
    if (params?.search) searchParams.set('search', params.search)
    if (params?.status) searchParams.set('status', params.status.join(','))

    const query = searchParams.toString()
    return fetchAPI(`/api/backlinks${query ? `?${query}` : ''}`)
  },

  // Get backlink analytics
  analytics: async (): Promise<{
    total: number
    by_status: Record<string, number>
    by_publisher: Record<string, number>
    total_cost: number
    avg_qc_score: number
  }> => {
    return fetchAPI('/api/backlinks/analytics')
  },

  // Generate similar backlink
  generateSimilar: async (backlinkId: string): Promise<JobPackage> => {
    return fetchAPI<JobPackage>(`/api/backlinks/${backlinkId}/generate-similar`, {
      method: 'POST',
    })
  },
}

// Settings API
export const settingsAPI = {
  // Get user settings
  get: async (): Promise<UserSettings> => {
    return fetchAPI<UserSettings>('/api/settings')
  },

  // Update user settings
  update: async (settings: Partial<UserSettings>): Promise<UserSettings> => {
    return fetchAPI<UserSettings>('/api/settings', {
      method: 'PATCH',
      body: JSON.stringify(settings),
    })
  },

  // Test API key
  testAPIKey: async (provider: string, apiKey: string): Promise<boolean> => {
    const result = await fetchAPI<{ valid: boolean }>('/api/settings/test-key', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key: apiKey }),
    })
    return result.valid
  },
}

// Stats API
export const statsAPI = {
  // Get dashboard stats
  dashboard: async (): Promise<{
    total_jobs: number
    delivered: number
    blocked: number
    aborted: number
    total_cost: number
    avg_cost_per_job: number
    avg_duration: number
    recent_jobs: JobPackage[]
  }> => {
    return fetchAPI('/api/stats/dashboard')
  },

  // Get cost breakdown
  costs: async (params?: {
    start_date?: string
    end_date?: string
    group_by?: 'day' | 'week' | 'month'
  }): Promise<{
    total: number
    by_provider: Record<string, number>
    by_strategy: Record<string, number>
    timeline: Array<{ date: string; cost: number }>
  }> => {
    const searchParams = new URLSearchParams()
    if (params?.start_date) searchParams.set('start_date', params.start_date)
    if (params?.end_date) searchParams.set('end_date', params.end_date)
    if (params?.group_by) searchParams.set('group_by', params.group_by)

    const query = searchParams.toString()
    return fetchAPI(`/api/stats/costs${query ? `?${query}` : ''}`)
  },
}

export { APIError }
