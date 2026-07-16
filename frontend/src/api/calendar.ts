import client from './client'

export interface CalendarEvent {
  id?: number
  time: string
  title: string
  type: string
  date?: string
  event_time?: string | null
  activity_id?: number
}

export function getCalendarEvents(month?: string) {
  return client.get<{ events: CalendarEvent[] }>('/calendar/events', { params: month ? { month } : {} })
}

export function addActivityToCalendar(activityId: number) {
  return client.post('/calendar/events', { poster_id: activityId })
}

export function removeActivityFromCalendar(activityId: number) {
  return client.delete(`/calendar/events/${activityId}`)
}

export function downloadActivityIcs(activityId: number) {
  return client.get(`/posters/${activityId}/ics`, { responseType: 'blob' })
}

/** 根据活动数量返回热度色 (GitHub 风格, 4 级) */
export function heatColor(count: number, isToday: boolean): string {
  if (isToday) return ''  // 今天由 CSS border 处理
  if (count === 0) return ''
  if (count === 1) return '#d4ece2'
  if (count <= 3) return '#7fbf9c'
  return '#0d5e3c'
}

/** 热度色深到需要白字 */
export function heatTextColor(count: number): string {
  return count >= 4 ? '#fff' : ''
}
