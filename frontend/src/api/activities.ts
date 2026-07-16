import client from './client'
import type { ActivityStatus, ApiPage } from './types'

export interface Attachment {
  id?: string
  name: string
  url: string
  mime_type?: string
  size?: number
}

export interface Activity {
  id: number
  title: string
  raw_text: string
  summary: string
  event_time: string | null
  location: string | null
  organizer: string | null
  status: ActivityStatus
  activity_type: string | null
  created_at: string
  reject_reason?: string
  cover_image_url?: string | null
}

export interface ActivityDetail extends Activity {
  tags?: string[]
  attachments?: Attachment[]
  meta?: {
    views: number
    registrations: number
  }
  favorite?: boolean
  registered?: boolean
  in_calendar?: boolean
  source_url?: string
  source_name?: string
  content_html?: string | null
}

export interface ActivityForm {
  title: string
  summary: string
  raw_text: string
  event_time: string | null
  location: string | null
  organizer: string | null
  activity_type: string | null
  tags: string[]
  attachments: Attachment[]
  cover_image_url?: string | null
}

export interface ActivityListParams {
  q?: string
  status?: string
  page?: number
  per_page?: number
  activity_type?: string
  sort?: 'created_at' | 'event_time'
}

export function listActivities(params?: ActivityListParams) {
  return client.get<ApiPage<Activity>>(
    '/activities',
    { params },
  )
}

export function getActivityById(id: number) {
  return client.get<ActivityDetail>(`/activities/${id}`)
}

export function registerForActivity(id: number) {
  return client.post<{ success: boolean; registrations: number; already_registered: boolean; registered?: boolean }>(`/activities/${id}/register`)
}

export function cancelRegistration(id: number) {
  return client.delete<{ success: boolean; registrations: number; registered: boolean }>(`/activities/${id}/register`)
}

export function setActivityFavorite(id: number, favorite: boolean) {
  return client.request<{ favorite: boolean }>({ method: favorite ? 'POST' : 'DELETE', url: `/activities/${id}/favorite` })
}

export function listMyActivities(params?: ActivityListParams) {
  return client.get<ApiPage<Activity>>('/activities/mine', { params })
}

export function createActivity(data: ActivityForm) {
  return client.post<ActivityDetail>('/activities', data)
}

export function updateActivity(id: number, data: ActivityForm) {
  return client.put<ActivityDetail>(`/activities/${id}`, data)
}

export function submitActivityForReview(id: number) {
  return client.post<ActivityDetail>(`/activities/${id}/submit-review`)
}
