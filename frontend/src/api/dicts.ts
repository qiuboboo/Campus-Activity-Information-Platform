import client from './client'

export type DictCategory = 'place' | 'org' | 'topic'

export interface DictEntry {
  id: number
  category: DictCategory | string
  standard_name: string
  aliases?: string | null
  description?: string | null
  created_at?: string
  updated_at?: string
}

export interface DictPage {
  category: string
  items: DictEntry[]
  page: number
  per_page: number
  total: number
}

export const listDictEntries = (category: DictCategory, params?: { q?: string; page?: number; per_page?: number }) => client.get<DictPage>(`/dict/${category}`, { params })
export const createDictEntry = (category: DictCategory, data: Pick<DictEntry, 'standard_name' | 'aliases' | 'description'>) => client.post<{ item: DictEntry }>(`/dict/${category}`, data)
export const updateDictEntry = (category: DictCategory, id: number, data: Partial<Pick<DictEntry, 'standard_name' | 'aliases' | 'description'>>) => client.put<{ item: DictEntry }>(`/dict/${category}/${id}`, data)
export const deleteDictEntry = (category: DictCategory, id: number) => client.delete(`/dict/${category}/${id}`)
export const getDictSuggestions = (category: string) => client.get<{ items: Array<{ value: string; count: number }> }>(`/dict/${category}/suggestions`)
export const seedDictEntries = () => client.post<{ seeded: number }>('/dict/seed')
