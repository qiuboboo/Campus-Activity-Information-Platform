import client from './client'
import type { Activity } from './activities'

export function getFeaturedActivities() {
  return client.get<{ items: Activity[] }>('/home/featured')
}
