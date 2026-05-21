<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listDataSources, triggerCrawl, type DataSource } from '@/api/datasources'
import { ElMessage, ElMessageBox } from 'element-plus'

const sources = ref<DataSource[]>([])
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

function formatTime(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(fetchData)
</script>

<template>
  <div>
    <h2 style="margin-bottom: 16px; color: #303133;">数据源管理</h2>

    <el-card shadow="hover" style="border-radius: 8px;">
      <el-table :data="sources" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="base_url" label="地址" min-width="250" show-overflow-tooltip />
        <el-table-column prop="source_level" label="级别" width="90">
          <template #default="{ row }">
            <el-tag
              :type="row.source_level === 'official' ? 'success' : row.source_level === 'internal' ? 'primary' : 'info'"
              size="small"
            >
              {{ row.source_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'" size="small">
              {{ row.enabled ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_success_at" label="最后成功" width="150">
          <template #default="{ row }">{{ formatTime(row.last_success_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :loading="crawling.has(row.id)"
              @click="handleCrawl(row.id)"
            >
              抓取
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
