import { describe, expect, it } from 'vitest'
import { safeAttachmentUrl, validateAttachmentFile } from './attachments'
import { sortActivities } from './activitySort'

describe('activity delivery guards', () => {
  it('only accepts safe attachment URL schemes', () => {
    expect(safeAttachmentUrl('/api/uploads/1/content')).toBe('/api/uploads/1/content')
    expect(safeAttachmentUrl('https://example.com/file.pdf')).toBe('https://example.com/file.pdf')
    expect(safeAttachmentUrl('javascript:alert(1)')).toBeNull()
    expect(safeAttachmentUrl('data:text/html,test')).toBeNull()
    expect(safeAttachmentUrl('//untrusted.example/file')).toBeNull()
  })

  it('enforces the selected attachment policy', () => {
    expect(validateAttachmentFile(new File(['ok'], 'agenda.pdf', { type: 'application/pdf' }))).toBeNull()
    expect(validateAttachmentFile(new File(['bad'], 'payload.html', { type: 'text/html' }))).toContain('仅支持')
    expect(validateAttachmentFile(new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'large.pdf', { type: 'application/pdf' }))).toContain('10 MB')
  })

  it('sorts latest publications and upcoming events deterministically', () => {
    const activities: any[] = [
      { id: 1, created_at: '2026-05-20T00:00:00', event_time: '2026-07-01T00:00:00' },
      { id: 2, created_at: '2026-05-22T00:00:00', event_time: null },
      { id: 3, created_at: '2026-05-21T00:00:00', event_time: '2026-06-01T00:00:00' },
    ]
    expect(sortActivities(activities, 'created_at').map(item => item.id)).toEqual([2, 3, 1])
    expect(sortActivities(activities, 'event_time').map(item => item.id)).toEqual([3, 1, 2])
  })
})
