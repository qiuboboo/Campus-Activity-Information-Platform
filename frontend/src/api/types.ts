export type UserRole = 'viewer' | 'publisher' | 'admin'
export type ActivityStatus = 'draft' | 'pending_review' | 'published' | 'rejected'

export interface ApiPage<T> {
  items: T[]
  page: number
  per_page: number
  total: number
  pages?: number
}

export interface ApiMessage {
  message: string
}

export interface UserProfile {
  id: number
  username: string
  role: UserRole
  email?: string
  created_at: string
  display_name?: string
}
