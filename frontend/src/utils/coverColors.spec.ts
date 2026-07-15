import { describe, expect, it } from 'vitest'
import { coverTheme, DEFAULT_COVER_GLYPH } from './coverColors'

describe('coverTheme', () => {
  it('returns a distinct gradient per canonical category', () => {
    const categories = ['讲座', '晚会', '竞赛', '论坛', '展览', '招聘', '体育', '其他']
    const gradients = categories.map((c) => coverTheme(c).gradient)
    expect(new Set(gradients).size).toBe(categories.length)
    for (const gradient of gradients) {
      expect(gradient).toMatch(/^linear-gradient\(135deg/)
    }
  })

  it('matches categories fuzzily when the value contains a canonical keyword', () => {
    expect(coverTheme('学术讲座')).toEqual(coverTheme('讲座'))
    expect(coverTheme('电竞比赛竞赛')).toEqual(coverTheme('竞赛'))
  })

  it('falls back to the default theme for unknown or empty categories', () => {
    const fallback = coverTheme(null)
    expect(coverTheme('')).toEqual(fallback)
    expect(coverTheme('不存在的分类')).toEqual(fallback)
    expect(fallback.glyph).toBe(DEFAULT_COVER_GLYPH)
  })

  it('uses the first character of the matched category as the watermark glyph', () => {
    expect(coverTheme('讲座').glyph).toBe('讲')
    expect(coverTheme('体育').glyph).toBe('体')
  })
})
