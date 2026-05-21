import client from './client'

export interface DataSource {
  id: number
  name: string
  base_url: string
  list_selector: string | null
  content_selector: string | null
  enabled: boolean
  crawl_mode: string
  source_level: string
  owner: string | null
  notes: string | null
  allowed_domains: string | null
  request_interval: number
  last_success_at: string | null
  last_failure_at: string | null
  last_error_message: string | null
  created_at: string
  updated_at: string
}

export interface CrawlLog {
  id: number
  data_source_id: number
  status: string
  message: string | null
  started_at: string
  finished_at: string | null
  pages_found: number
  pages_succeeded: number
  pages_failed: number
  duplicates_skipped: number
  drafts_created: number
  average_quality_score: number | null
}

export function listDataSources() {
  return client.get<{ items: DataSource[] }>('/data-sources')
}

export function getDataSource(id: number) {
  return client.get<DataSource>(`/data-sources/${id}`)
}

export function createDataSource(data: Record<string, unknown>) {
  return client.post<DataSource>('/data-sources', data)
}

export function updateDataSource(id: number, data: Record<string, unknown>) {
  return client.put<DataSource>(`/data-sources/${id}`, data)
}

export function triggerCrawl(id: number, sync = false) {
  return client.post(`/data-sources/${id}/crawl`, { sync })
}

export function getCrawlLogs(id: number) {
  return client.get<{ items: CrawlLog[] }>(`/data-sources/${id}/logs`)
}
