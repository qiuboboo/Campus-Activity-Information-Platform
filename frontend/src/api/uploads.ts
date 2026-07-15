import client from './client'
import type { Attachment } from './activities'

export function uploadAttachment(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return client.post<Attachment>('/uploads', formData)
}

export function deleteUpload(id: string) {
  return client.delete(`/uploads/${encodeURIComponent(id)}`)
}
