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
