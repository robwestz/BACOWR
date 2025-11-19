// Core Types for BACOWR Frontend
// Aligned with backend BacklinkJobPackage schema

export type JobStatus = 'PENDING' | 'RUNNING' | 'DELIVERED' | 'BLOCKED' | 'ABORTED'
export type QCStatus = 'PASS' | 'PASS_WITH_AUTOFIX' | 'BLOCKED'
export type LLMProvider = 'anthropic' | 'openai' | 'google' | 'auto'
export type WritingStrategy = 'multi_stage' | 'single_shot'
export type IntentClassification = 'informational' | 'commercial_research' | 'transactional' | 'navigational'
export type BridgeType = 'strong' | 'pivot' | 'wrapper'
export type AnchorType = 'exact' | 'partial' | 'brand' | 'generic'

// Job Package Types
export interface JobInput {
  publisher_domain: string
  target_url: string
  anchor_text: string
  llm_provider?: LLMProvider
  strategy?: WritingStrategy
  country?: string
  use_ahrefs?: boolean
  enable_llm_profiling?: boolean
}

export interface JobMeta {
  job_id: string
  created_at: string
  spec_version: string
  status: JobStatus
  execution_time?: number
}

export interface PublisherProfile {
  domain: string
  url: string
  language: string
  tone: string
  editorial_style: string
  typical_topics: string[]
}

export interface TargetProfile {
  url: string
  title: string
  language: string
  intent: IntentClassification
  main_topics: string[]
  entities: string[]
}

export interface AnchorProfile {
  text: string
  type: AnchorType
  risk_level: 'low' | 'medium' | 'high'
  intent: IntentClassification
}

export interface SERPResult {
  position: number
  url: string
  title: string
  snippet: string
}

export interface SERPResearch {
  main_query: string
  serp_intent: IntentClassification
  top_results: SERPResult[]
  cluster_queries: string[]
  lsi_terms: string[]
}

export interface IntentExtension {
  target_intent: IntentClassification
  serp_intent: IntentClassification
  anchor_intent: IntentClassification
  alignment: 'aligned' | 'partial' | 'off'
  recommended_bridge: BridgeType
  forbidden_angles: string[]
}

export interface GenerationConstraints {
  language: string
  min_word_count: number
  max_word_count: number
  tone: string
  bridge_type: BridgeType
  lsi_terms: string[]
}

export interface QCIssue {
  category: string
  severity: 'high' | 'medium' | 'low'
  description: string
  auto_fixable: boolean
  fixed: boolean
}

export interface AutoFixLog {
  issue_id: string
  action: string
  before: string
  after: string
  timestamp: string
}

export interface QCReport {
  status: QCStatus
  overall_score: number
  issues: QCIssue[]
  autofix_logs: AutoFixLog[]
  human_signoff_required: boolean
  blocking_reasons: string[]
}

export interface ExecutionLog {
  metadata: {
    job_id: string
    started_at: string
    completed_at: string
    final_state: string
  }
  log_entries: Array<{
    type: string
    timestamp: string
    from_state?: string
    to_state?: string
    message?: string
  }>
}

export interface JobMetrics {
  generation: {
    duration_seconds: number
    llm_calls: number
    cost_usd: number
    tokens_used: number
  }
  quality: {
    qc_score: number
    issues_found: number
    issues_fixed: number
  }
}

export interface JobPackage {
  job_meta: JobMeta
  input_minimal: JobInput
  publisher_profile: PublisherProfile
  target_profile: TargetProfile
  anchor_profile: AnchorProfile
  serp_research_extension: SERPResearch
  intent_extension: IntentExtension
  generation_constraints: GenerationConstraints
  article?: string
  qc_report?: QCReport
  execution_log?: ExecutionLog
  metrics?: JobMetrics
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: any
  }
}

export interface JobListResponse {
  jobs: JobPackage[]
  total: number
  page: number
  per_page: number
}

export interface BacklinkRecord {
  id: string
  publisher: string
  target: string
  anchor: string
  article_url?: string
  created_at: string
  status: JobStatus
  qc_score?: number
  cost_usd?: number
}

export interface BatchJob {
  batch_id: string
  name: string
  total_jobs: number
  completed_jobs: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  started_at?: string
  completed_at?: string
  jobs: JobPackage[]
}

// Batch Review Types (Day 2 QA Workflow)
export type BatchReviewStatus =
  | 'pending'
  | 'processing'
  | 'ready_for_review'
  | 'in_review'
  | 'completed'
  | 'failed'

export type ReviewItemStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'needs_regeneration'
  | 'regenerating'
  | 'regenerated'

export interface BatchReview {
  id: string
  name: string
  description?: string
  status: BatchReviewStatus
  created_at: string
  updated_at: string
  user_id: string
  job_ids: string[]
  batch_config?: Record<string, any>
  stats: {
    total_items: number
    pending: number
    approved: number
    rejected: number
    needs_regeneration: number
    regenerating: number
    regenerated: number
  }
}

export interface BatchReviewItem {
  id: string
  batch_id: string
  job_id: string
  review_status: ReviewItemStatus
  qc_snapshot: {
    article_text: string
    qc_score: number
    qc_status: QCStatus
    word_count: number
    issues_found: number
  }
  reviewer_notes?: string
  reviewed_at?: string
  regeneration_count: number
  created_at: string
  updated_at: string
}

export interface BatchReviewListResponse {
  batches: BatchReview[]
  total: number
  page: number
  per_page: number
}

export interface BatchReviewItemsResponse {
  items: BatchReviewItem[]
  total: number
}

export interface ReviewDecision {
  decision: 'approve' | 'reject' | 'needs_regeneration'
  reviewer_notes?: string
}

export interface BatchExportResponse {
  batch_id: string
  batch_name: string
  export_format: string
  export_date: string
  approved_items: Array<{
    job_id: string
    article_text: string
    publisher_domain: string
    target_url: string
    anchor_text: string
    qc_score: number
  }>
  stats: {
    total_approved: number
    total_items: number
    approval_rate: number
  }
}

// WebSocket Event Types
export interface WSJobUpdate {
  job_id: string
  status: JobStatus
  progress: number
  message: string
  timestamp: string
}

// UI State Types
export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
}

export interface FilterState {
  status?: JobStatus[]
  llm_provider?: LLMProvider[]
  date_range?: {
    start: Date
    end: Date
  }
  search?: string
}

// Settings Types
export interface UserSettings {
  api_keys: {
    anthropic?: string
    openai?: string
    google?: string
    ahrefs?: string
  }
  defaults: {
    llm_provider: LLMProvider
    strategy: WritingStrategy
    country: string
    use_ahrefs: boolean
    enable_llm_profiling: boolean
  }
  cost_limits: {
    enabled: boolean
    daily_limit_usd?: number
    per_job_limit_usd?: number
  }
  notifications: {
    email?: string
    webhook_url?: string
    enable_email: boolean
    enable_webhook: boolean
  }
}
