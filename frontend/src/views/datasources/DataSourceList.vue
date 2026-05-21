<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listDataSources, triggerCrawl, getCrawlLogs, type DataSource, type CrawlLog } from '@/api/datasources'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const sources = ref<DataSource[]>([])
const crawlLogs = ref<Map<number, CrawlLog[]>>(new Map())
const expandedRows = ref<Set<number>>(new Set())
const loading = ref(false)
const crawling = ref<Set<number>>(new Set())

async function fetchData() {
  loading.value = true
  try {
    const res = await listDataSources()
    sources.value = res.data.items
  } finally {
    loading.value = false
  }
}

async function handleCrawl(id: number) {
  try {
    await ElMessageBox.confirm('确定要触发该数据源的爬虫吗？', '确认', {
      confirmButtonText: '开始抓取',
      cancelButtonText: '取消',
    })
    crawling.value.add(id)
    const res = await triggerCrawl(id, true) // sync mode for simplicity
    if (res.data.success) {
      ElMessage.success(`抓取完成，创建 ${res.data.posters_created} 条草稿`)
    } else {
      ElMessage.error(res.data.error || '抓取失败')
    }
  } catch {
    // cancelled or error
  } finally {
    crawling.value.delete(id)
    fetchData()
  }
}

async function toggleExpand(id: number) {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id)
    return
  }
  expandedRows.value.add(id)
  if (!crawlLogs.value.has(id)) {
    try {
      const res = await getCrawlLogs(id)
      crawlLogs.value.set(id, res.data.items)
    } catch {
      crawlLogs.value.set(id, [])
    }
  }
}

function goCreate() {
  router.push('/datasources/create')
}

function goEdit(id: number) {
  router.push(`/datasources/${id}/edit`)
}

function formatTime(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(fetchData)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h2 style="color: #303133;">数据源管理</h2>
      <el-button type="primary" @click="goCreate">
        <el-icon style="margin-right: 4px;"><Plus /></el-icon>新建数据源
      </el-button>
    </div>

    <el-card shadow="hover" style="border-radius: 8px;">
      <el-table :data="sources" v-loading="loading" stripe @expand-change="(row: DataSource) => toggleExpand(row.id)">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div style="padding: 12px;">
              <h4 style="margin-bottom: 8px; color: #606266;">抓取日志</h4>
              <el-table
                v-if="crawlLogs.get(row.id)?.length"
                :data="crawlLogs.get(row.id)!"
                size="small"
                stripe
              >
                <el-table-column prop="started_at" label="开始时间" width="160">
                  <template #default="{ row: log }">{{ formatTime(log.started_at) }}</template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row: log }">
                    <el-tag
                      :type="log.status === 'success' ? 'success' : log.status === 'running' ? 'warning' : 'danger'"
                      size="small"
                    >
                      {{ log.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="pages_found" label="发现" width="60" align="center" />
                <el-table-column prop="pages_succeeded" label="成功" width="60" align="center" />
                <el-table-column prop="drafts_created" label="新建" width="60" align="center" />
                <el-table-column prop="average_quality_score" label="质量分" width="70" align="center" />
                <el-table-column prop="message" label="消息" min-width="150" show-overflow-tooltip />
              </el-table>
              <el-empty v-else description="暂无抓取日志" :image-size="80" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="130" />
        <el-table-column prop="base_url" label="地址" min-width="220" show-overflow-tooltip />
        <el-table-column prop="source_level" label="级别" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.source_level === 'official' ? 'success' : row.source_level === 'internal' ? 'primary' : 'info'"
              size="small"
            >
              {{ row.source_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用" width="60" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'" size="small">
              {{ row.enabled ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_success_at" label="最后成功" width="140">
          <template #default="{ row }">{{ formatTime(row.last_success_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :loading="crawling.has(row.id)"
              @click="handleCrawl(row.id)"
            >
              抓取
            </el-button>
            <el-button size="small" @click="goEdit(row.id)">
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
