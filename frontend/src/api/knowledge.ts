import client from './client'

export interface KnowledgeNode {
  id: number
  name: string
  alias: string | null
  node_type: string
  description: string | null
  source_url: string | null
  created_at: string
  updated_at: string
}

export function listKnowledgeNodes(params?: { q?: string; node_type?: string }) {
  return client.get<{ items: KnowledgeNode[] }>('/knowledge/nodes', { params })
}

export function getKnowledgeNode(id: number) {
  return client.get(`/knowledge/nodes/${id}`)
}

export function rebuildKnowledge(data?: { status?: string; source_type?: string }) {
  return client.post('/knowledge/rebuild', data || {})
}
