import type {
  AssistantApplyPatchRequest,
  AssistantApplyPatchResponse,
  AssistantChatRequest,
  AssistantChatResponse,
  AssistantMessagesResponse,
  AssistantSessionsResponse,
} from '../types/discovery'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export class ApiError extends Error {
  status: number
  details: unknown
  constructor(status: number, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

export async function parseApiError(res: Response): Promise<ApiError> {
  const text = await res.text()
  try {
    const json = JSON.parse(text)
    const humanMessage = json?.human_message || json?.detail?.human_message || json?.detail?.error || json?.error || 'Ошибка запроса к backend'
    return new ApiError(res.status, humanMessage, json?.details || json?.detail || json)
  } catch {
    const msg = text.includes('Failed to fetch') ? 'Backend недоступен. Запустите backend на порту 8000 или проверьте VITE_API_URL.' : `Ошибка backend (${res.status})`
    return new ApiError(res.status, msg, text)
  }
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!res.ok) throw await parseApiError(res)
  return res.json()
}

export async function apiForm<T>(path: string, body: FormData): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { method: 'POST', body })
  if (!res.ok) throw await parseApiError(res)
  return res.json()
}

export const assistantApi = {
  sendMessage(projectId: string, payload: AssistantChatRequest) {
    return api<AssistantChatResponse>(`/projects/${projectId}/assistant/chat`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  listSessions(projectId: string) {
    return api<AssistantSessionsResponse>(`/projects/${projectId}/assistant/sessions`)
  },
  listMessages(projectId: string, sessionId: string) {
    return api<AssistantMessagesResponse>(`/projects/${projectId}/assistant/sessions/${sessionId}/messages`)
  },
  applyPatch(projectId: string, payload: AssistantApplyPatchRequest) {
    return api<AssistantApplyPatchResponse>(`/projects/${projectId}/assistant/apply-patch`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
