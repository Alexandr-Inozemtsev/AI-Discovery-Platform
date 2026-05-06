export type ProjectStatus = 'DRAFT' | 'IN_PROGRESS' | 'BT_READY' | 'APPROVED'
export type ProjectStage = 'CONTEXT' | 'PROBLEM' | 'GOAL' | 'BUSINESS_EFFECT' | 'AS_IS' | 'TO_BE' | 'USE_CASES' | 'REQUIREMENTS' | 'RISKS' | 'FINAL_BT' | 'VALIDATION_REPORT'
export type ArtifactType = 'CONTEXT' | 'PROBLEM' | 'GOAL' | 'BUSINESS_EFFECT' | 'AS_IS' | 'TO_BE' | 'USE_CASES' | 'FUNCTIONAL_REQUIREMENTS' | 'NON_FUNCTIONAL_REQUIREMENTS' | 'RISKS' | 'GLOSSARY' | 'FINAL_BT' | 'VALIDATION_REPORT'

export interface Project { id: string; project_name: string; business_domain?: string; status: ProjectStatus; current_stage: ProjectStage; jira_epic_url?: string }
export interface Artifact { id: string; project_id: string; artifact_type: ArtifactType; content: string; structured_content?: Record<string, unknown>; version: number }
