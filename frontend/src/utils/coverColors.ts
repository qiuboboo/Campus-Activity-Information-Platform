/**
 * 活动封面占位主题:按活动分类映射品牌协调的双色渐变与水印字。
 * 色板刻意保持同一明度区间 (深→中),白色文字在任意档位可读,
 * 色相编码分类:学术绿 / 论坛墨蓝 / 竞赛靛青 / 晚会绛紫 / 展览黛紫 / 招聘深青 / 体育赭橙。
 */
export interface CoverTheme {
  gradient: string
  glyph: string
}

export const DEFAULT_COVER_GLYPH = '活'

const gradient = (from: string, to: string) => `linear-gradient(135deg, ${from}, ${to})`

const COVER_THEMES: Array<{ keys: string[]; theme: CoverTheme }> = [
  { keys: ['讲座', '讲坛', '报告'], theme: { gradient: gradient('#0d5e3c', '#1e7a4e'), glyph: '讲' } },
  { keys: ['论坛', '沙龙'], theme: { gradient: gradient('#1c3d5d', '#33608c'), glyph: '论' } },
  { keys: ['竞赛', '比赛', '大赛'], theme: { gradient: gradient('#14495c', '#2a7d8c'), glyph: '竞' } },
  { keys: ['晚会', '演出', '文艺'], theme: { gradient: gradient('#5b2340', '#8c3f63'), glyph: '晚' } },
  { keys: ['展览', '展示'], theme: { gradient: gradient('#3a2e63', '#5d4f96'), glyph: '展' } },
  { keys: ['招聘', '宣讲'], theme: { gradient: gradient('#0f4f4a', '#2c7d70'), glyph: '招' } },
  { keys: ['体育', '运动'], theme: { gradient: gradient('#7a4014', '#b0662a'), glyph: '体' } },
  { keys: ['其他'], theme: { gradient: gradient('#3f5462', '#5f7d90'), glyph: '其' } },
]

const DEFAULT_THEME: CoverTheme = { gradient: gradient('#41544a', '#66806f'), glyph: DEFAULT_COVER_GLYPH }

export function coverTheme(category?: string | null): CoverTheme {
  const value = (category || '').trim()
  if (!value) return DEFAULT_THEME
  for (const { keys, theme } of COVER_THEMES) {
    if (keys.some((key) => value === key || value.includes(key))) return theme
  }
  return DEFAULT_THEME
}
