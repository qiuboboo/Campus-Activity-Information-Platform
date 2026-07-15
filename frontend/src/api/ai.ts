import client from './client'

export interface AiStatus {
  llm_configured: boolean
  mcp_servers: unknown
}

export interface ExtractedActivityFields {
  title?: string
  summary?: string
  raw_text?: string
  event_time?: string | null
  location?: string
  organizer?: string
  activity_type?: string
  tags?: string[] | string
  [key: string]: unknown
}

export interface AiSearchResult {
  title?: string
  summary?: string
  url?: string
  source?: string
  [key: string]: unknown
}

export const getAiStatus = () => client.get<AiStatus>('/ai/status')
export const extractActivityFields = (text: string, model?: string) => client.post<{ fields: ExtractedActivityFields }>('/ai/extract', { text, model })
export const enrichPosterWithAi = (posterId: number) => client.post(`/ai/enrich/${posterId}`)
export const searchWithAi = (query: string, sources?: string[]) => client.post<{ query: string; results: AiSearchResult[]; count: number }>('/ai/search', { query, sources })
export const listMcpServers = () => client.get<{ servers: unknown }>('/ai/mcp/servers')
export const callMcpTool = (server: string, tool: string, params: Record<string, unknown>) => client.post('/ai/mcp/call', { server, tool, params })
