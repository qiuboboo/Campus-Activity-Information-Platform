import client from './client'

export interface Activity {
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

export interface ActivityDetail extends Activity {
  tags?: string[]
  attachments?: Array<{ url: string; name: string }>
  meta?: {
    views: number
    registrations: number
  }
}

export interface ActivityListParams {
  q?: string
  status?: string
  page?: number
  per_page?: number
}

export function listActivities(params?: ActivityListParams) {
  return client.get<{ items: Activity[]; page: number; per_page: number; total: number }>(
    '/activities',
    { params },
  )
}

export function getActivityById(id: number) {
  return client.get<ActivityDetail>(`/activities/${id}`)
}
