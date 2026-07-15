import client from './client'
import type { Activity } from './activities'
import type { ApiPage } from './types'

export interface SearchParams {
  q: string
  page?: number
  per_page?: number
  activity_type?: string
  sort?: 'relevance' | 'created_at' | 'event_time' | 'title'
}

export interface SearchResult {
  hit_type: 'activity' | 'external'
  item: Activity
  score?: number
  source?: string
  url?: string
}

export interface SearchResponse extends Omit<ApiPage<SearchResult>, 'items'> {
  items: SearchResult[]
  search_mode: string
}

export function searchActivities(scope: 'internal' | 'external', params: SearchParams) {
  return client.get<SearchResponse>(`/search/${scope}`, { params })
}
