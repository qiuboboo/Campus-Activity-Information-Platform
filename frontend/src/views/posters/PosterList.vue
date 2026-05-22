<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listPosters, type Poster } from '@/api/posters'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const posters = ref<Poster[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const statusFilter = ref('')
const loading = ref(false)

const statusOptions = [
  { value: '', label: '全部' },
  { value: 'draft', label: '草稿' },
  { value: 'pending_review', label: '待审核' },
  { value: 'published', label: '已发布' },
  { value: 'rejected', label: '已拒绝' },
]

function statusTag(row: Poster) {
  const map: Record<string, string> = {
    draft: 'info',
    pending_review: 'warning',
    published: 'success',
    rejected: 'danger',
  }
  return map[row.status] || 'info'
}

function statusLabel(row: Poster) {
  const map: Record<string, string> = {
    draft: '草稿',
    pending_review: '待审核',
    published: '已发布',
    rejected: '已拒绝',
  }
  return map[row.status] || row.status
}

async function fetchData() {
  loading.value = true
  try {
    const res = await listPosters({
      q: keyword.value || undefined,
      status: statusFilter.value || undefined,
      page: page.value,
      per_page: pageSize.value,
    })
    posters.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function goDetail(id: number) {
  router.push(`/posters/${id}`)
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
      <h2 style="color: #303133;">活动海报</h2>
      <el-button type="primary" @click="router.push('/posters/create')" v-if="auth.isPublisher">
        <el-icon style="margin-right: 4px;"><Plus /></el-icon>创建海报
      </el-button>
    </div>

    <el-card shadow="hover" style="border-radius: 8px;">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input v-model="keyword" placeholder="标题/摘要/正文" clearable style="width: 200px;" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="statusFilter" style="width: 120px" clearable>
            <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :icon="'Search'">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="posters"
        v-loading="loading"
        stripe
        @row-click="(row: Poster) => goDetail(row.id)"
        style="cursor: pointer;"
      >
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="event_time" label="活动时间" width="160">
          <template #default="{ row }">{{ formatTime(row.event_time) }}</template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="140" show-overflow-tooltip />
        <el-table-column prop="organizer" label="主办方" width="130" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTag(row)" size="small">{{ statusLabel(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quality_score" label="质量" width="70" align="center">
          <template #default="{ row }">
            <span v-if="row.quality_score != null">{{ row.quality_score }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="fetchData"
        />
      </div>
    </el-card>
  </div>
</template>
