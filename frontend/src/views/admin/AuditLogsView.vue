<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import { exportActivities, exportCrawlReport, exportKnowledge, getAuditLogs, type AuditLog } from '@/api/admin'

const loading = ref(false)
const error = ref('')
const logs = ref<AuditLog[]>([])
const action = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    logs.value = (await getAuditLogs(action.value ? { action: action.value } : undefined)).data.items
  } catch (e: any) {
    error.value = e?.response?.data?.message || '审计日志加载失败'
  } finally {
    loading.value = false
  }
}

async function download(kind: 'activities' | 'knowledge' | 'crawl') {
  const response = kind === 'activities' ? await exportActivities() : kind === 'knowledge' ? await exportKnowledge() : await exportCrawlReport()
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = kind === 'activities' ? 'activities.json' : kind === 'knowledge' ? 'knowledge.json' : 'crawl-report.json'
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出已开始')
}

onMounted(load)
</script>

<template>
  <AppShell title="审计日志">
    <template #heading>
      <el-button @click="download('activities')">导出活动</el-button>
      <el-button @click="download('knowledge')">导出知识</el-button>
      <el-button type="primary" @click="download('crawl')">导出爬取报告</el-button>
    </template>

    <section class="toolbar surface-card">
      <el-select v-model="action" clearable placeholder="全部操作" @change="load">
        <el-option label="批准" value="approve" />
        <el-option label="驳回" value="reject" />
        <el-option label="抓取" value="crawl" />
        <el-option label="知识重建" value="rebuild" />
      </el-select>
    </section>

    <PageState :loading="loading" :error="error" :empty="!loading && !error && !logs.length" empty-text="暂无审计记录" @retry="load">
      <section class="surface-card table-wrap">
        <el-table :data="logs">
          <el-table-column prop="created_at" label="时间" min-width="170" />
          <el-table-column prop="actor" label="操作人" width="120" />
          <el-table-column prop="action" label="操作" width="140" />
          <el-table-column prop="target" label="目标" min-width="160" />
          <el-table-column prop="summary" label="摘要" min-width="220" />
        </el-table>
      </section>
    </PageState>
  </AppShell>
</template>

<style scoped>
.toolbar { padding: 14px; margin-bottom: 16px; }
.table-wrap { overflow: auto; }
</style>
