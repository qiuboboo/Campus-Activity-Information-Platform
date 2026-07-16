const RELATION_LABELS: Record<string, string> = {
  has_org: '主办方',
  has_topic: '主题',
  has_place: '地点',
  has_time: '时间',
  has_source: '来源',
  same_day: '同一天',
  same_place: '同地点',
  same_org: '同主办方',
  same_topic: '同主题',
  rule: '规则匹配',
  manual: '手动关联',
}

export function relationLabel(key: string): string {
  return RELATION_LABELS[key] || key
}

export function matchedByLabel(key: string): string {
  return RELATION_LABELS[key] || key
}
