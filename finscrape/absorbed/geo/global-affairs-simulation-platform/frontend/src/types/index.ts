// 类型定义

export interface RawNews {
  news_id: string
  title: string
  source_name: string
  source_type: string
  published_at: string | null
  region_tags: string[]
  raw_entities: { countries: string[]; persons: string[]; organizations: string[]; locations: string[] }
  cluster_id: string | null
  status: string
  url: string
  body?: string
}

export interface NewsCluster {
  cluster_id: string
  cluster_title: string
  news_count: number
  related_news_ids: string[]
  time_window_start: string | null
  time_window_end: string | null
  key_actors: string[]
  key_locations: string[]
  primary_issue: string
  secondary_issues: string[]
  escalation_signals: string[]
  deescalation_signals: string[]
  evidence_summary: string
  cluster_confidence: number
  event_id: string | null
  created_at: string | null
  news?: RawNews[]
}

export interface AbstractIRGEvent {
  event_id: string
  event_title: string
  event_type: EventType
  stage_of_crisis: CrisisStage
  key_actors: string[]
  actor_roles: Record<string, string>
  key_locations: string[]
  strategic_dimensions: string[]
  driving_forces: string[]
  constraints: string[]
  immediate_triggers: string[]
  current_balance: string
  major_risks: string[]
  current_opportunities: string[]
  event_confidence: number
  /** Claude失败时规则引擎回退生成，质量较低 */
  is_fallback?: boolean
  geo_coordinates: { lat: number; lng: number } | null
  region: string
  source_cluster_ids: string[]
  status: string
  created_at: string | null
}

export type EventType =
  | 'military_escalation'
  | 'diplomatic_negotiation'
  | 'economic_coercion'
  | 'energy_shipping_risk'
  | 'alliance_realignment'
  | 'domestic_political_spillover'
  | 'information_psychological_operations'

export type CrisisStage =
  | 'latent' | 'emergence' | 'escalation' | 'crisis'
  | 'de_escalation' | 'resolution' | 'post_crisis'

export type DirectionType = 'escalation' | 'stalemate' | 'de_escalation'

export interface TheoryAnalysis {
  analysis_id: string
  event_id: string
  theory_name: string
  theory_display_name: string
  core_assumption: string
  interpretation: string
  main_drivers: string[]
  likely_actor_responses: Record<string, string>
  escalation_implications: string[]
  deescalation_implications: string[]
  weaknesses: string[]
  counterarguments: string[]
  confidence_note: string
  created_at: string | null
}

export interface ScenarioStep {
  step_id: string
  script_id: string
  step_number: number
  title: string
  why_this_step_happens: string
  which_actor_acts_first: string
  how_other_actors_react: Record<string, string>
  key_drivers: string[]
  constraints: string[]
  supporting_evidence: string[]
  counter_evidence: string[]
  uncertainty: string
  impact_on_next_step: string
  node_type: string
}

export interface ScenarioScript {
  script_id: string
  event_id: string
  run_id: string | null
  direction_type: DirectionType
  script_title: string
  script_description: string
  why_this_script_is_realistic: string
  trigger_conditions: string[]
  invalidation_conditions: string[]
  supporting_factors: string[]
  opposing_factors: string[]
  probability_low: number | null
  probability_high: number | null
  probability_central: number | null
  confidence_level: string
  uncertainty_notes: string
  is_branch: boolean
  created_at: string | null
  steps?: ScenarioStep[]
}

export interface PredictionRun {
  run_id: string
  event_id: string
  root_question: string
  model_version: string
  rules_version: string
  summary: string
  status: string
  script_ids: string[]
  is_branch: boolean
  created_at: string | null
  scripts?: ScenarioScript[]
}

export interface BranchRequest {
  base_run_id: string
  hypothesis_type: string
  hypothesis_title: string
  hypothesis_description: string
  affected_actors: string[]
  expected_direction: DirectionType
}

export interface BranchRun {
  branch_run_id: string
  base_run_id: string
  event_id: string
  hypothesis_type: string
  hypothesis_title: string
  hypothesis_description?: string
  expected_direction: DirectionType
  status: string
  diff_summary: string | null
  created_at: string | null
}

export interface ScenarioSummary {
  has_scenarios: boolean
  script_count: number
  escalation: number | null
  stalemate: number | null
  de_escalation: number | null
}

export interface GlobePoint {
  event_id: string
  event_title: string
  event_type: EventType
  stage_of_crisis: CrisisStage
  lat: number
  lng: number
  region: string
  key_actors: string[]
  actor_roles: Record<string, string>
  event_confidence: number
  scenario_summary?: ScenarioSummary
}

export type RelationshipType = 
  | 'shared_actor' 
  | 'same_region' 
  | 'causal_chain' 
  | 'escalation_cascade' 
  | 'semantic_similar' 
  | 'actor_conflict'

export interface GlobeRelationship {
  from: string
  to: string
  type: RelationshipType
  actors: string[]
  weight: number
  metadata?: Record<string, unknown>
}

// 名称映射
export const EVENT_TYPE_LABELS: Record<EventType, string> = {
  military_escalation: '军事升级',
  diplomatic_negotiation: '外交谈判',
  economic_coercion: '经济胁迫',
  energy_shipping_risk: '能源航运风险',
  alliance_realignment: '联盟重组',
  domestic_political_spillover: '国内政治溢出',
  information_psychological_operations: '信息心理战',
}

export const CRISIS_STAGE_LABELS: Record<CrisisStage, string> = {
  latent: '潜伏期',
  emergence: '浮现期',
  escalation: '升级期',
  crisis: '危机期',
  de_escalation: '降级期',
  resolution: '解决期',
  post_crisis: '后危机期',
}

export const DIRECTION_LABELS: Record<DirectionType, string> = {
  escalation: '升级方向',
  stalemate: '僵持方向',
  de_escalation: '缓和方向',
}

export const DIRECTION_CONFIG: Record<DirectionType, { label: string; color: string; hex: string; bg: string; border: string; dot: string }> = {
  escalation: { label: '升级', color: 'text-red-400', hex: '#ef4444', bg: 'bg-red-900/30', border: 'border-red-700/50', dot: 'bg-red-500' },
  stalemate: { label: '僵持', color: 'text-amber-400', hex: '#f59e0b', bg: 'bg-amber-900/30', border: 'border-amber-700/50', dot: 'bg-amber-500' },
  de_escalation: { label: '缓和', color: 'text-emerald-400', hex: '#10b981', bg: 'bg-emerald-900/30', border: 'border-emerald-700/50', dot: 'bg-emerald-500' },
}

export const EVENT_TYPE_COLORS: Record<EventType, string> = {
  military_escalation: '#ef4444',
  diplomatic_negotiation: '#3b82f6',
  economic_coercion: '#f59e0b',
  energy_shipping_risk: '#f97316',
  alliance_realignment: '#8b5cf6',
  domestic_political_spillover: '#ec4899',
  information_psychological_operations: '#06b6d4',
}

// --- 历史类比 ---
export interface MatchedCase {
  case_id: string
  title: string
  year: number
  event_type: string
  region: string
  similarity_score: number
  structural_similarities: string[]
  key_differences: string[]
  historical_outcome: string
  outcome_direction: string
  historical_base_rates: { escalation: number; stalemate: number; de_escalation: number }
  probability_adjustment: string
  key_lessons: string[]
  tags: string[]
}

export interface AnalogyResult {
  analogy_id: string
  event_id: string
  matched_cases: MatchedCase[]
  synthesis: string
  historical_base_rate: { escalation: number; stalemate: number; de_escalation: number }
  unique_modern_factors: string[]
  total_cases_searched: number
  generated_at: string | null
  status?: string
}

export interface HistoricalCase {
  case_id: string
  title: string
  title_en: string
  year: number | null
  duration_days: number | null
  event_type: string
  region: string
  crisis_stage_peak: string
  key_actors: string[]
  actor_roles: Record<string, string>
  primary_issue: string
  strategic_dimensions: string[]
  key_triggers: string[]
  key_constraints: string[]
  escalation_path: string[]
  resolution: string
  resolution_type: string
  outcome_summary: string
  key_lessons: string[]
  analogous_features: string[]
  probability_realized: { escalation: number; stalemate: number; de_escalation: number }
  actual_outcome_direction: string
  prediction_accuracy_notes: string
  tags: string[]
  created_at?: string | null
  updated_at?: string | null
}

// --- 预测校准 ---
export interface CalibrationSummary {
  total_evaluations: number
  script_hit_rate: number
  avg_node_hit_rate: number
  avg_brier_score: number
  calibration_grade: string
  combined_score: number
  error_distribution: Record<string, number>
  by_event_type: Record<string, { count: number; hit_rate: number; avg_brier: number }>
  by_crisis_stage: Record<string, { count: number; hit_rate: number }>
  time_trend: Array<{ month: string; hit_rate: number; count: number }>
  theory_accuracy: Record<string, { count: number; hit_rate: number }>
  improvement_suggestions: string[]
  message?: string
}

export interface RunCalibrationDetail {
  run_id: string
  event_id: string
  event_title: string
  status: string
  scripts: Array<{
    script_id: string
    title: string
    direction: string
    probability_central: number | null
    brier_score: number | null
    hit: boolean | null
  }>
  evaluation: {
    script_hit: boolean
    node_hit_rate: number | null
    main_error_category: string | null
    detailed_error_analysis: string
    correct_aspects: string[]
    incorrect_aspects: string[]
    suggested_adjustments: string[]
  } | null
  outcome: {
    actual_summary: string
    actual_event_type: string
    matched_script_id: string | null
  } | null
}

export interface TheoryCalibration {
  [theory: string]: {
    count: number
    hit_rate: number
    event_ids: string[]
  }
}

export interface DirectionCalibration {
  [direction: string]: {
    total: number
    hit: number
    hit_rate: number
  }
}

// --- 新闻源类型 ---

export interface NewsSourceInfo {
  source_id: string
  source_name: string
  source_type: string
  region: string
  language: string
  enabled: boolean
  polling_interval_minutes: number
  max_per_fetch: number
  tags: string[]
  description: string
  feed_url: string
}

export interface SourceTestResult {
  source_id: string
  source_name: string
  status: 'ok' | 'error' | 'not_tested'
  fetched: number
  saved: number
  error?: string | null
}

// --- 事件版本管理 ---
export interface EventVersion {
  version_id: string
  event_id: string
  version_number: number
  snapshot: Record<string, unknown>
  change_source: string
  change_summary: string
  created_at: string | null
}

export interface FieldChange {
  field: string
  old: unknown
  new: unknown
}

export interface IngestionSourceResult {
  source_id: string
  source_name: string
  fetched: number
  saved: number
  skipped_dup: number
  status: 'ok' | 'error'
  error?: string | null
}

export interface IngestionDetail {
  total_fetched: number
  total_saved: number
  total_skipped_dup: number
  total_failed_sources: number
  data_status: string
  source_results: IngestionSourceResult[]
  errors: string[]
}

// --- 批注与讨论 ---
export type AnnotationEntityType = 'event' | 'script' | 'theory' | 'analogy' | 'run'
export type AnnotationImportance = 'low' | 'medium' | 'high'

export interface Annotation {
  annotation_id: string
  entity_type: AnnotationEntityType
  entity_id: string
  content: string
  tags: string[]
  importance: AnnotationImportance
  version: string
  history_count: number
  created_at: string | null
  updated_at: string | null
  /** GET /{id}时才有 */
  history?: Array<{
    version: string
    content: string
    tags: string[]
    importance: string
    saved_at: string
  }>
  access_log?: Array<{ action: string; ts: string }>
}

export interface AnnotationCreate {
  entity_type: AnnotationEntityType
  entity_id: string
  content: string
  tags?: string[]
  importance?: AnnotationImportance
}

export interface AnnotationUpdate {
  content: string
  tags?: string[]
  importance?: AnnotationImportance
}
export type PipelineTaskStatus = 'pending' | 'running' | 'done' | 'error'
export type PipelineStepStatus = 'idle' | 'running' | 'done' | 'error'

export interface PipelineTaskStep {
  key: string
  label: string
  status: PipelineStepStatus
  started_at?: string | null
  finished_at?: string | null
  duration_seconds?: number | null
}

export interface PipelineTaskStatusResponse {
  task_id: string
  status: PipelineTaskStatus
  created_at?: string | null
  started_at?: string | null
  updated_at?: string | null
  finished_at?: string | null
  running_seconds?: number | null
  progress_detail?: string | null
  sub_progress?: { current: number; total: number; label: string } | null
  steps: PipelineTaskStep[]
  result?: Record<string, unknown> | null
  error?: string | null
}
