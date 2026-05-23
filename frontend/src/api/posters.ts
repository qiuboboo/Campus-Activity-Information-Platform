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
  activity_type: string | null
  created_at: string
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
