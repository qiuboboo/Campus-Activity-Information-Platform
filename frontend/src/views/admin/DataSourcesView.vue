<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import {
  createDataSource,
  getDataSourceLogs,
  getDataSources,
  getTaskStatus,
  runDataSource,
  toggleDataSource,
  updateDataSource,
  type CrawlLog,
  type DataSource,
  type TaskStatus,
} from '@/api/admin'

const loading = ref(false)
const error = ref('')
const sources = ref<DataSource[]>([])
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  name: '',
  url: '',
  enabled: true,
  list_selector: '',
  content_selector: '',
  allowed_domains: '',
  crawl_mode: 'basic',
  source_level: 'official',
})
const logsDialog = ref(false)
const logsLoading = ref(false)
const activeSource = ref<DataSource | null>(null)
const logs = ref<CrawlLog[]>([])
const taskId = ref('')
const taskStatus = ref<TaskStatus | null>(null)
let taskTimer: ReturnType<typeof setInterval> | null = null

async function load() {
  loading.value = true
  error.value = ''
  try {
    sources.value = (await getDataSources()).data.items
  } catch (e: any) {
    error.value = e?.response?.data?.message || '数据源加载失败'
  } finally {
    loading.value = false
  }
}

async function toggle(source: DataSource) {
  try {
    await ElMessageBox.confirm(`确认${source.enabled ? '停用' : '启用'}“${source.name}”吗？`, '变更数据源状态', { type: 'warning' })
    await toggleDataSource(source.id, !source.enabled)
    source.enabled = !source.enabled
    ElMessage.success('状态已更新')
  } catch {}
}

async function run(source: DataSource) {
  try {
    await ElMessageBox.confirm(`确认立即抓取“${source.name}”吗？`, '启动抓取任务', { type: 'warning' })
    const { data }: any = await runDataSource(source.id)
    if (data.task_id) {
      taskId.value = data.task_id
      taskStatus.value = { task_id: data.task_id, state: 'PENDING', result: null, error: null }
      source.last_status = '异步任务已创建'
      ElMessage.success('抓取任务已创建，正在自动刷新状态')
      startTaskPolling(source)
    } else {
      source.last_status = data.message || '抓取完成'
      ElMessage.success(source.last_status)
    }
    openLogs(source)
  } catch {}
}

function open(source?: DataSource) {
  editingId.value = source?.id || null
  Object.assign(form, source ? {
    name: source.name,
    url: source.url,
    enabled: source.enabled,
    list_selector: source.list_selector || '',
    content_selector: source.content_selector || '',
    allowed_domains: source.allowed_domains || domainFromUrl(source.url),
    crawl_mode: source.crawl_mode || 'basic',
    source_level: source.source_level || 'official',
  } : {
    name: '',
    url: '',
    enabled: true,
    list_selector: '',
    content_selector: '',
    allowed_domains: '',
    crawl_mode: 'basic',
    source_level: 'official',
  })
  dialog.value = true
}

async function save() {
  try {
    if (editingId.value) await updateDataSource(editingId.value, form)
    else await createDataSource(form)
    dialog.value = false
    ElMessage.success('数据源已保存')
    load()
  } catch {}
}

async function openLogs(source: DataSource) {
  activeSource.value = source
  logsDialog.value = true
  logsLoading.value = true
  try {
    logs.value = (await getDataSourceLogs(source.id)).data.items
  } finally {
    logsLoading.value = false
  }
}

async function refreshTask() {
  if (!taskId.value.trim()) return ElMessage.warning('请输入任务 ID')
  const { data } = await getTaskStatus(taskId.value.trim())
  taskStatus.value = data
}

function stopTaskPolling() {
  if (taskTimer) {
    clearInterval(taskTimer)
    taskTimer = null
  }
}

function startTaskPolling(source?: DataSource) {
  stopTaskPolling()
  taskTimer = setInterval(async () => {
    if (!taskId.value.trim()) return
    try {
      await refreshTask()
      const state = taskStatus.value?.state
      if (state === 'SUCCESS' || state === 'FAILURE') {
        stopTaskPolling()
        if (source) await openLogs(source)
        await load()
        ElMessage[state === 'SUCCESS' ? 'success' : 'error'](state === 'SUCCESS' ? '抓取任务已完成' : '抓取任务失败')
      }
    } catch {
      stopTaskPolling()
    }
  }, 2500)
}

function formatTime(value?: string | null) {
  return value ? new Date(value).toLocaleString('zh-CN') : '-'
}

function domainFromUrl(value?: string | null) {
  try {
    return value ? new URL(value).hostname : ''
  } catch {
    return ''
  }
}

onMounted(load)
onUnmounted(stopTaskPolling)
</script>

<template>
  <AppShell title="数据源管理">
    <template #heading>
      <el-button type="primary" @click="open()">新建数据源</el-button>
    </template>

    <section class="task-panel surface-card">
      <el-input v-model="taskId" clearable placeholder="任务 ID" />
      <el-button type="primary" @click="refreshTask">刷新任务状态</el-button>
      <el-tag v-if="taskStatus" :type="taskStatus.state === 'SUCCESS' ? 'success' : taskStatus.state === 'FAILURE' ? 'danger' : 'warning'">
        {{ taskStatus.state }}
      </el-tag>
      <span v-if="taskStatus?.error" class="task-error">{{ taskStatus.error }}</span>
    </section>

    <PageState :loading="loading" :error="error" :empty="!loading && !error && !sources.length" empty-text="暂无数据源" @retry="load">
      <section class="surface-card table-wrap">
        <el-table :data="sources">
          <el-table-column prop="name" label="名称" min-width="160" />
          <el-table-column prop="url" label="地址" min-width="260" />
          <el-table-column label="启用" width="100">
            <template #default="{ row }"><el-switch :model-value="row.enabled" @change="toggle(row)" /></template>
          </el-table-column>
          <el-table-column prop="last_status" label="最近状态" min-width="150" />
          <el-table-column label="操作" width="250">
            <template #default="{ row }">
              <el-button text type="primary" @click="open(row)">编辑</el-button>
              <el-button text type="primary" @click="run(row)">抓取</el-button>
              <el-button text type="primary" @click="openLogs(row)">日志</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </PageState>

    <el-dialog v-model="dialog" :title="editingId ? '编辑数据源' : '新建数据源'" width="min(92vw, 520px)">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.url" @blur="form.allowed_domains ||= domainFromUrl(form.url)" /></el-form-item>
        <el-form-item label="列表链接选择器"><el-input v-model="form.list_selector" placeholder="例如 a，留空则只抓当前页面" /></el-form-item>
        <el-form-item label="正文选择器"><el-input v-model="form.content_selector" placeholder="例如 article、.content，留空则抓整页文本" /></el-form-item>
        <el-form-item label="允许域名"><el-input v-model="form.allowed_domains" placeholder="例如 www.sysu.edu.cn，多个域名用逗号分隔" /></el-form-item>
        <el-form-item label="来源级别">
          <el-select v-model="form.source_level" style="width: 100%">
            <el-option label="官方来源" value="official" />
            <el-option label="外部来源" value="external" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="logsDialog" size="min(92vw, 720px)" :title="activeSource ? `${activeSource.name} 抓取日志` : '抓取日志'">
      <PageState :loading="logsLoading" :empty="!logsLoading && !logs.length" empty-text="暂无抓取日志">
        <div class="log-list">
          <article v-for="log in logs" :key="log.id" class="log-item">
            <div>
              <strong>{{ log.status }}</strong>
              <span>{{ formatTime(log.started_at) }} - {{ formatTime(log.finished_at) }}</span>
            </div>
            <p>{{ log.message || '无消息' }}</p>
            <dl>
              <dt>发现</dt><dd>{{ log.pages_found }}</dd>
              <dt>成功</dt><dd>{{ log.pages_succeeded }}</dd>
              <dt>失败</dt><dd>{{ log.pages_failed }}</dd>
              <dt>新草稿</dt><dd>{{ log.drafts_created }}</dd>
              <dt>去重</dt><dd>{{ log.duplicates_skipped }}</dd>
            </dl>
          </article>
        </div>
      </PageState>
    </el-drawer>
  </AppShell>
</template>

<style scoped>
.task-panel { padding: 14px; margin-bottom: 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.task-panel :deep(.el-input) { max-width: 360px; }
.task-error { color: #c45656; }
.table-wrap { overflow: auto; }
.log-list { display: grid; gap: 12px; }
.log-item { border: 1px solid var(--line); border-radius: 8px; padding: 14px; }
.log-item > div { display: flex; justify-content: space-between; gap: 12px; color: var(--brand-dark); }
.log-item span, .log-item p { color: var(--text-muted); }
.log-item p { margin: 10px 0; }
dl { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; margin: 0; }
dt { color: var(--text-muted); font-size: 12px; }
dd { margin: 0; font-weight: 700; color: var(--brand-dark); }
@media (max-width: 640px) { dl { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
