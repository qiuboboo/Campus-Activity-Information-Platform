import client from './client'

export interface CalendarEvent {
  time: string
  title: string
  type: string
}

export function getCalendarEvents() {
  return client.get<{ events: CalendarEvent[] }>('/calendar/events')
}
