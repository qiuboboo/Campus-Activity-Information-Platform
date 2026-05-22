<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listAuditLogs, type AuditLog } from '@/api/audit_logs'

const logs = ref<AuditLog[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const actionFilter = ref('')
const typeFilter = ref('')
const loading = ref(false)

const actionOptions = [
  { value: '', label: '全部操作' },
  { value: 'create_poster', label: '创建海报' },
  { value: 'update_poster', label: '更新海报' },
  { value: 'approve_poster', label: '批准海报' },
  { value: 'reject_poster', label: '驳回海报' },
  { value: 'submit_poster', label: '提交审核' },
  { value: 'trigger_crawl', label: '触发爬虫' },
  { value: 'rebuild_knowledge', label: '重建知识' },
  { value: 'merge_poster', label: '合并海报' },
]

const typeOptions = [
  { value: '', label: '全部类型' },
  { value: 'poster', label: '海报' },
  { value: 'data_source', label: '数据源' },
  { value: 'knowledge', label: '知识图谱' },
  { value: 'system', label: '系统' },
]

const actionLabels: Record<string, string> = {}
for (const opt of actionOptions) {
  if (opt.value) actionLabels[opt.value] = opt.label
}

async function fetchData() {
  loading.value = true
  try {
    const res = await listAuditLogs({
      action: actionFilter.value || undefined,
      target_type: typeFilter.value || undefined,
      page: page.value,
      per_page: pageSize.value,
    })
    logs.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(fetchData)
</script>

<template>
  <div>
    <h2 style="margin-bottom: 16px; color: #303133;">审计日志</h2>

    <el-card shadow="hover" style="border-radius: 8px;">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="操作类型">
          <el-select v-model="actionFilter" style="width: 140px" clearable>
            <el-option v-for="opt in actionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标类型">
          <el-select v-model="typeFilter" style="width: 120px" clearable>
            <el-option v-for="opt in typeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :icon="'Search'">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="actor_name" label="操作人" width="100" />
        <el-table-column prop="action" label="操作" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ actionLabels[row.action] || row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="目标类型" width="90" />
        <el-table-column prop="summary" label="摘要" min-width="300" show-overflow-tooltip />
        <el-table-column prop="target_id" label="目标 ID" width="80" align="center" />
      </el-table>

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @change="fetchData"
        />
      </div>
    </el-card>
  </div>
</template>
