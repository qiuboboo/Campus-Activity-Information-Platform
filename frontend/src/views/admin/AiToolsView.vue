<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import { callMcpTool, enrichPosterWithAi, extractActivityFields, getAiStatus, listMcpServers, searchWithAi, type AiSearchResult, type AiStatus, type ExtractedActivityFields } from '@/api/ai'

const loading = ref(false)
const error = ref('')
const status = ref<AiStatus>()
const mcpServers = ref<unknown>()
const rawText = ref('')
const model = ref('')
const extracted = ref<ExtractedActivityFields>()
const posterId = ref<number>()
const enrichResult = ref<unknown>()
const aiQuery = ref('')
const aiSources = ref('')
const aiResults = ref<AiSearchResult[]>([])
const mcp = reactive({ server: '', tool: '', params: '{}' })
const mcpResult = ref<unknown>()

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [statusRes, serversRes] = await Promise.all([getAiStatus(), listMcpServers()])
    status.value = statusRes.data
    mcpServers.value = serversRes.data.servers
  } catch (e: any) {
    error.value = e?.response?.data?.message || 'AI 状态加载失败'
  } finally {
    loading.value = false
  }
}

async function extract() {
  if (!rawText.value.trim()) return ElMessage.warning('请先输入活动原文')
  const { data } = await extractActivityFields(rawText.value.trim(), model.value || undefined)
  extracted.value = data.fields
  ElMessage.success('字段抽取完成')
}

async function enrich() {
  if (!posterId.value) return ElMessage.warning('请输入活动 ID')
  const { data } = await enrichPosterWithAi(posterId.value)
  enrichResult.value = data
  ElMessage.success('AI 增强完成')
}

async function aiSearch() {
  if (!aiQuery.value.trim()) return ElMessage.warning('请输入搜索关键词')
  const sources = aiSources.value.split(/[,，\n]/).map((item) => item.trim()).filter(Boolean)
  const { data } = await searchWithAi(aiQuery.value.trim(), sources.length ? sources : undefined)
  aiResults.value = data.results
}

async function callTool() {
  if (!mcp.server.trim() || !mcp.tool.trim()) return ElMessage.warning('请输入 MCP server 和 tool')
  let params: Record<string, unknown>
  try {
    params = JSON.parse(mcp.params || '{}')
  } catch {
    return ElMessage.error('params 必须是合法 JSON')
  }
  const { data } = await callMcpTool(mcp.server.trim(), mcp.tool.trim(), params)
  mcpResult.value = data
}

onMounted(load)
</script>

<template>
  <AppShell title="AI 工具">
    <PageState :loading="loading" :error="error" @retry="load">
      <section class="status-row">
        <article class="surface-card status-card">
          <span>LLM 配置</span>
          <strong>{{ status?.llm_configured ? '已配置' : '未配置' }}</strong>
        </article>
        <article class="surface-card status-card">
          <span>MCP 服务</span>
          <strong>{{ mcpServers ? '可查看' : '无配置' }}</strong>
        </article>
      </section>

      <section class="admin-grid">
        <article class="surface-card panel">
          <h2>文本抽取活动字段</h2>
          <el-input v-model="model" placeholder="模型配置，可留空" />
          <el-input v-model="rawText" type="textarea" :rows="8" placeholder="粘贴活动通知原文" />
          <el-button type="primary" @click="extract">抽取字段</el-button>
          <pre v-if="extracted">{{ JSON.stringify(extracted, null, 2) }}</pre>
        </article>

        <article class="surface-card panel">
          <h2>活动 AI 增强</h2>
          <el-input-number v-model="posterId" :min="1" placeholder="活动 ID" />
          <el-button type="primary" @click="enrich">增强活动</el-button>
          <pre v-if="enrichResult">{{ JSON.stringify(enrichResult, null, 2) }}</pre>
        </article>

        <article class="surface-card panel">
          <h2>AI 搜索</h2>
          <el-input v-model="aiQuery" placeholder="搜索关键词" @keyup.enter="aiSearch" />
          <el-input v-model="aiSources" placeholder="来源限制，用逗号分隔，可留空" />
          <el-button type="primary" @click="aiSearch">搜索</el-button>
          <div v-if="aiResults.length" class="result-list">
            <article v-for="(item, index) in aiResults" :key="index" class="result-item">
              <strong>{{ item.title || `结果 ${index + 1}` }}</strong>
              <p>{{ item.summary }}</p>
              <a v-if="item.url" :href="item.url" target="_blank" rel="noreferrer">{{ item.source || item.url }}</a>
            </article>
          </div>
        </article>

        <article class="surface-card panel">
          <h2>MCP 调用</h2>
          <el-input v-model="mcp.server" placeholder="server" />
          <el-input v-model="mcp.tool" placeholder="tool" />
          <el-input v-model="mcp.params" type="textarea" :rows="5" placeholder='{"query":"校园活动"}' />
          <el-button type="primary" @click="callTool">调用工具</el-button>
          <pre v-if="mcpResult">{{ JSON.stringify(mcpResult, null, 2) }}</pre>
        </article>
      </section>
    </PageState>
  </AppShell>
</template>

<style scoped>
.status-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-bottom: 18px; }
.status-card { padding: 18px; display: grid; gap: 6px; }
.status-card span { color: var(--text-muted); }
.status-card strong { color: var(--brand-dark); font-size: 22px; }
.admin-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.panel { padding: 20px; display: grid; gap: 12px; align-content: start; }
.panel h2 { margin: 0; color: var(--brand-dark); font-size: 18px; }
pre { max-height: 320px; overflow: auto; margin: 0; padding: 12px; border-radius: 8px; background: #f5f8f6; color: #22352c; font-size: 12px; }
.result-list { display: grid; gap: 10px; }
.result-item { padding: 12px 0; border-top: 1px solid var(--line); }
.result-item p { color: var(--text-muted); margin: 6px 0; line-height: 1.6; }
.result-item a { color: var(--brand); }
@media (max-width: 820px) { .status-row, .admin-grid { grid-template-columns: 1fr; } }
</style>
