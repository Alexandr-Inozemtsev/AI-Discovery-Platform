export type ProjectStatus = 'DRAFT' | 'IN_PROGRESS' | 'BT_READY' | 'APPROVED'
export type ProjectStage = 'CONTEXT' | 'PROBLEM' | 'GOAL' | 'BUSINESS_EFFECT' | 'AS_IS' | 'TO_BE' | 'USE_CASES' | 'REQUIREMENTS' | 'RISKS' | 'FINAL_BT' | 'VALIDATION_REPORT'
export type ArtifactType = 'CONTEXT' | 'PROBLEM' | 'GOAL' | 'BUSINESS_EFFECT' | 'AS_IS' | 'TO_BE' | 'USE_CASES' | 'FUNCTIONAL_REQUIREMENTS' | 'NON_FUNCTIONAL_REQUIREMENTS' | 'RISKS' | 'GLOSSARY' | 'FINAL_BT' | 'VALIDATION_REPORT'

export interface Project { id: string; project_name: string; business_domain?: string; status: ProjectStatus; current_stage: ProjectStage; jira_epic_url?: string }
export interface Artifact { id: string; project_id: string; artifact_type: ArtifactType; content: string; structured_content?: Record<string, unknown>; version: number }

export type ContextReadinessStatus = 'ready' | 'warning' | 'blocked'
export interface ContextCoverage {
  manual_context: boolean
  documents: boolean
  systems: boolean
  processes: boolean
  roles: boolean
  integrations: boolean
  bpmn: boolean
  kpi: boolean
  sla: boolean
  constraints: boolean
}
export interface ContextReadiness {
  status: ContextReadinessStatus
  score: number
  can_go_to_problem: boolean
  summary: string
  blocking_reasons: string[]
  warnings: string[]
  next_actions: string[]
}

export type AssistantMessageRole = 'user' | 'assistant' | 'system' | 'tool'

export interface AssistantSession {
  id: string
  project_id: string
  title: string
  status: string
  created_at: string
  updated_at: string
}

export interface AssistantMessage {
  id: string
  project_id: string
  session_id: string
  role: AssistantMessageRole
  content: string
  payload?: Record<string, unknown> | null
  created_at: string
}

export interface AssistantAction {
  id: string
  project_id: string
  session_id: string
  message_id: string
  action_type: string
  target_artifact_type?: ArtifactType | null
  status: 'proposed' | 'applied' | 'rejected' | string
  proposed_patch?: Record<string, unknown>
  preview?: Record<string, unknown>
  result?: Record<string, unknown>
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface AssistantChatRequest {
  message: string
  session_id?: string | null
  artifact_type?: ArtifactType | null
  context?: Record<string, unknown> | null
}

export interface AssistantChatResponse {
  ok: boolean
  session_id: string
  user_message: AssistantMessage
  assistant_message: AssistantMessage
  intent?: Record<string, unknown>
  action?: AssistantAction | null
  preview?: Record<string, unknown> | null
  warnings?: string[]
  errors?: string[]
}

export interface AssistantSessionsResponse {
  ok: boolean
  sessions: AssistantSession[]
}

export interface AssistantMessagesResponse {
  ok: boolean
  messages: AssistantMessage[]
}

export interface AssistantApplyPatchRequest {
  session_id: string
  action_id: string
}

export interface AssistantApplyPatchResponse {
  ok: boolean
  artifact: Artifact
  action: AssistantAction
}
