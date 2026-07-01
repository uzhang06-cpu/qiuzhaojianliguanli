/* ── Pipeline 状态定义 ────────────────────────────────────────────── */

export const PIPELINE_STAGES = [
  { key: 'interested',        label: '意向待投',   order: 0, color: '#6366f1' },
  { key: 'applied',           label: '已投递',     order: 1, color: '#3b82f6' },
  { key: 'assessment',        label: '笔试 / 测评', order: 2, color: '#f59e0b' },
  { key: 'ai_interview',      label: 'AI面',       order: 3, color: '#8b5cf6' },
  { key: 'human_interview',   label: '人工面试',   order: 4, color: '#06b6d4' },
  { key: 'offer_evaluation',  label: 'Offer 评估', order: 5, color: '#22c55e' },
  { key: 'archived',          label: '归档池',     order: 6, color: '#6b7280' },
] as const;

export type PipelineKey = (typeof PIPELINE_STAGES)[number]['key'];

/* ── Position 数据类型 ────────────────────────────────────────────── */

export interface Position {
  id: number;
  company: string;
  position: string;
  status: string;
  status_label: string;
  base_location?: string;
  salary_range?: string;
  job_description?: string;
  next_ddl?: string;        // ISO datetime
  interview_link?: string;
  interview_platform?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

/* ── Agent 结果类型 ────────────────────────────────────────────────── */

export interface DisplayField {
  key: string;
  label: string;
  value: any;
  confidence: number;
  editable: boolean;
  highlight: boolean;
}

export interface SkillResult {
  skill: string;
  success: boolean;
  entities: any[];
  raw_output: string;
  error?: string;
}

export interface AgentResult {
  action_type: string;
  action_label: string;
  confidence: number;
  position_id?: number;
  display_fields: DisplayField[];
  needs_human_review: boolean;
  human_review_reason: string;
  raw_input: string;
  skill_results: SkillResult[];
  total_latency_ms: number;
}

/* ── 通知类型 ──────────────────────────────────────────────────────── */

export interface AppNotification {
  id: string;
  type: 'warning' | 'danger' | 'info' | 'success';
  title: string;
  message: string;
  position_id?: number;
  created_at: string;
  read: boolean;
}

/* ── 视图模式 ──────────────────────────────────────────────────────── */

export type ViewMode = 'kanban' | 'list';
