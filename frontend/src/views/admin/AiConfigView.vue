<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'

interface LlmProfile { name: string; model: string; base_url: string; key_masked: string }

const loading = ref(false)
const error = ref('')
const config = ref<{
  llm_configured: boolean; llm_profiles: LlmProfile[];
  searxng_base_url: string; searxng_engines: string[];
  embedding_enabled: boolean; mcp_servers: any[]
} | null>(null)

async function load() {
  loading.value = true; error.value = ''
  try {
    const token = localStorage.getItem('token')
    const resp = await fetch('/api/ai/status', { headers: { Authorization: `Bearer ${token || ''}` } })
    config.value = await resp.json()
  } catch { error.value = '配置加载失败' } finally { loading.value = false }
}

onMounted(load)
</script>

<template>
  <AppShell title="AI 配置">
    <PageState :loading="loading" :error="error" @retry="load">
      <section v-if="config" class="config-grid">
        <!-- LLM 配置 -->
        <div class="surface-card panel">
          <h2>LLM 模型</h2>
          <template v-if="config.llm_profiles.length">
            <article v-for="p in config.llm_profiles" :key="p.name" class="profile-card">
              <div class="profile-head">
                <strong>{{ p.name }}</strong>
                <el-tag size="small" type="success" effect="plain">已配置</el-tag>
              </div>
              <dl>
                <dt>模型</dt><dd>{{ p.model || '-' }}</dd>
                <dt>地址</dt><dd>{{ p.base_url }}</dd>
                <dt>密钥</dt><dd><code>{{ p.key_masked }}</code></dd>
              </dl>
            </article>
          </template>
          <el-empty v-else description="未配置 LLM" :image-size="60" />
        </div>

        <!-- 搜索配置 -->
        <div class="surface-card panel">
          <h2>外部搜索</h2>
          <dl>
            <dt>SearXNG 地址</dt><dd>{{ config.searxng_base_url || '未配置' }}</dd>
            <dt>可用引擎</dt><dd>{{ config.searxng_engines.join('、') }}</dd>
          </dl>
        </div>

        <!-- Embedding -->
        <div class="surface-card panel">
          <h2>Embedding</h2>
          <div class="status-line">
            <el-tag :type="config.embedding_enabled ? 'success' : 'info'" effect="plain">
              {{ config.embedding_enabled ? '已启用' : '未启用' }}
            </el-tag>
          </div>
        </div>

        <!-- MCP -->
        <div class="surface-card panel">
          <h2>MCP 服务</h2>
          <template v-if="config.mcp_servers.length">
            <article v-for="srv in config.mcp_servers" :key="srv.name" class="profile-card">
              <div class="profile-head">
                <strong>{{ srv.name }}</strong>
                <el-tag size="small" :type="srv.status === 'connected' ? 'success' : 'warning'" effect="plain">{{ srv.status }}</el-tag>
              </div>
              <p v-if="srv.description" style="color:var(--text-muted);font-size:13px">{{ srv.description }}</p>
            </article>
          </template>
          <el-empty v-else description="未配置 MCP 服务" :image-size="60" />
        </div>
      </section>
    </PageState>
  </AppShell>
</template>

<style scoped>
.config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.panel { padding: 22px; }
.panel h2 { margin: 0 0 16px; font-size: 17px; color: var(--brand-dark); }
.profile-card { border-top: 1px solid var(--line); padding: 14px 0; }
.profile-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
dl { display: grid; grid-template-columns: 80px 1fr; gap: 6px 14px; }
dt { color: var(--text-muted); font-size: 13px; }
dd { color: var(--text-main); font-size: 13px; font-weight: 500; }
code { font-family: monospace; background: #f5f7f6; padding: 1px 5px; border-radius: 3px; font-size: 12px; }
.status-line { margin-top: 8px; }
</style>
