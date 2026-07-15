import type { Attachment } from '@/api/activities'

export const MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
export const ACCEPTED_ATTACHMENT_TYPES = new Set([
  'image/jpeg', 'image/png', 'image/webp', 'application/pdf',
  'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
])

export const ACCEPTED_ATTACHMENT_EXTENSIONS = '.jpg,.jpeg,.png,.webp,.pdf,.doc,.docx,.xls,.xlsx'

export function validateAttachmentFile(file: File): string | null {
  if (!ACCEPTED_ATTACHMENT_TYPES.has(file.type)) return '仅支持 JPG、PNG、WEBP、PDF、Word 和 Excel 文件'
  if (file.size > MAX_ATTACHMENT_SIZE) return '单个附件不能超过 10 MB'
  return null
}

/** Accept legacy relative paths and web URLs, never executable or data URL schemes. */
export function safeAttachmentUrl(value: string | null | undefined): string | null {
  if (!value) return null
  const trimmed = value.trim()
  if (trimmed.startsWith('/') && !trimmed.startsWith('//')) return trimmed
  try {
    const url = new URL(trimmed)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null
  } catch {
    return null
  }
}

export function isUploadedAttachment(attachment: Attachment) {
  return Boolean(attachment.id && safeAttachmentUrl(attachment.url))
}
