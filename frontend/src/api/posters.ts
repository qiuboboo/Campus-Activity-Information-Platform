import client from './client'

export interface Poster {
  id: number
  title: string
  raw_text: string
  summary: string
  event_time: string | null
  location: string | null
  organizer: string | null
  status: string
  source_type: string
  source_url: string | null
  review_comment: string | null
  created_by: number
  quality_score: number | null
  quality_notes: string | null
  tags: string | null
  activity_type: string | null
  content_html: string | null
  duplicate_group_key: string | null
  source_fingerprint: string | null
  last_crawled_at: string | null
  created_at: string
  updated_at: string
}

export interface PosterListParams {
  q?: string
  status?: string
  page?: number
  per_page?: number
}

export function listPosters(params?: PosterListParams) {
  return client.get<{ items: Poster[]; page: number; per_page: number; total: number }>(
    '/posters',
    { params },
  )
}

export function getPoster(id: number) {
  return client.get<{ item: Poster }>(`/posters/${id}`)
}

export function getRelated(id: number) {
  return client.get(`/posters/${id}/related`)
}

export function createPoster(data: Record<string, unknown>) {
  return client.post<{ item: Poster }>('/posters', data)
}

export function updatePoster(id: number, data: Record<string, unknown>) {
  return client.put<{ item: Poster }>(`/posters/${id}`, data)
}

export function submitPoster(id: number) {
  return client.post<{ item: Poster }>(`/posters/${id}/submit`)
}

export function reviewPoster(id: number, action: 'approve' | 'reject', comment?: string) {
  return client.post<{ item: Poster }>(`/posters/${id}/review`, { action, comment })
}

export function getReviewQueue(params: { status?: string; source_type?: string; page?: number; per_page?: number }) {
  return client.get<{ items: Poster[]; page: number; per_page: number; total: number }>(
    '/posters/review-queue',
    { params },
  )
}
