import client from './client'
import type { Activity } from './activities'
import type { ApiPage } from './types'

export interface CrawlSummary {
  id: number
  data_source_id: number
  status: string
  pages_found: number
  pages_succeeded: number
  pages_failed: number
  duplicates_skipped: number
  drafts_created: number
  average_quality_score: number | null
  started_at: string
  finished_at: string | null
}

export interface AdminSummary {
  pending: number
  published: number
  sources: number
  failed_tasks: number
  posters?: { total: number; published: number; draft: number; rejected: number }
  knowledge_nodes?: number
  poster_links?: number
  data_sources?: number
  last_crawl?: CrawlSummary | null
}
export interface AuditLog { id: number; created_at: string; actor: string; action: string; target: string; summary: string }
export interface DataSource {
  id: number
  name: string
  url: string
  enabled: boolean
  last_status: string
  list_selector?: string | null
  content_selector?: string | null
  allowed_domains?: string | null
  crawl_mode?: string
  source_level?: string
}
export interface CrawlLog {
  id: number
  data_source_id: number
  status: string
  message?: string
  started_at: string
  finished_at?: string | null
  pages_found: number
  pages_succeeded: number
  pages_failed: number
  duplicates_skipped: number
  drafts_created: number
}
export interface TaskStatus { task_id: string; state: string; result?: unknown; error?: string | null }
export interface DuplicateResponse { poster: Activity; duplicates: Activity[]; count: number }

export const getAdminSummary = () => client.get<AdminSummary>('/demo/summary')
export const getReviewActivities = (params?: Record<string, string | number>) => client.get<ApiPage<Activity>>('/posters/review-queue', { params })
export const reviewActivity = (id: number, action: 'approve' | 'reject', reason = '') => client.post(`/posters/${id}/review`, { action, reason })
export const bulkReviewActivities = (ids: number[], action: 'approve' | 'reject', comment = '') => client.post('/posters/bulk-review', { poster_ids: ids, action, comment })
export const getAuditLogs = (params?: Record<string, string | number>) => client.get<ApiPage<AuditLog>>('/audit-logs', { params })
export const getDataSources = () => client.get<{ items: DataSource[] }>('/data-sources')
export const createDataSource = (data: Partial<DataSource> & Pick<DataSource, 'name' | 'url'>) => client.post<DataSource>('/data-sources', data)
export const updateDataSource = (id: number, data: Partial<DataSource>) => client.put<DataSource>(`/data-sources/${id}`, data)
export const toggleDataSource = (id: number, enabled: boolean) => client.patch(`/data-sources/${id}`, { enabled })
export const runDataSource = (id: number, sync = false) => client.post(`/data-sources/${id}/crawl`, { sync })
export const getDataSourceLogs = (id: number) => client.get<{ items: CrawlLog[] }>(`/data-sources/${id}/logs`)
export const getTaskStatus = (taskId: string) => client.get<TaskStatus>(`/tasks/${encodeURIComponent(taskId)}`)
export const getPosterDuplicates = (id: number) => client.get<DuplicateResponse>(`/posters/${id}/duplicates`)
export const mergePosterSource = (id: number, sourcePosterId: number) => client.post(`/posters/${id}/merge-source`, { source_poster_id: sourcePosterId })
export const rebuildPosterKnowledge = (id: number) => client.post(`/posters/${id}/rebuild-knowledge`)
export const exportActivities = () => client.get('/export/posters.json', { responseType: 'blob' })
export const exportKnowledge = () => client.get('/export/knowledge.json', { responseType: 'blob' })
export const exportCrawlReport = () => client.get('/export/crawl-report.json', { responseType: 'blob' })
