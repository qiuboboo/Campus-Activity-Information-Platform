import client from './client'

export interface AuditLog {
  id: number
  actor_id: number
  actor_name: string
  action: string
  target_type: string
  target_id: number | null
  summary: string
  metadata: string | null
  created_at: string
}

export interface AuditLogListParams {
  actor_id?: number
  action?: string
  target_type?: string
  page?: number
  per_page?: number
}

export function listAuditLogs(params?: AuditLogListParams) {
  return client.get<{ items: AuditLog[]; page: number; per_page: number; total: number }>(
    '/audit-logs',
    { params },
  )
}
