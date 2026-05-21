<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getReviewQueue, reviewPoster, type Poster } from '@/api/posters'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const auth = useAuthStore()

const posters = ref<Poster[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

async function fetchData() {
  loading.value = true
  try {
    const res = await getReviewQueue({ page: page.value, per_page: pageSize.value })
    posters.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function handleReview(id: number, action: 'approve' | 'reject') {
  try {
    if (action === 'reject') {
      await ElMessageBox.prompt('请输入驳回原因', '驳回', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      })
      await reviewPoster(id, action, '')
    } else {
      await reviewPoster(id, action)
    }
    ElMessage.success(action === 'approve' ? '已批准' : '已驳回')
    fetchData()
  } catch {
    // cancelled or error
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
    <h2 style="margin-bottom: 16px; color: #303133;">审核队列</h2>

    <el-card shadow="hover" style="border-radius: 8px;">
      <el-table :data="posters" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="event_time" label="活动时间" width="150">
          <template #default="{ row }">{{ formatTime(row.event_time) }}</template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="130" show-overflow-tooltip />
        <el-table-column prop="organizer" label="主办方" width="120" show-overflow-tooltip />
        <el-table-column prop="quality_score" label="质量" width="60" align="center" />
        <el-table-column prop="source_type" label="来源" width="80" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              type="success"
              size="small"
              @click="handleReview(row.id, 'approve')"
              :disabled="row.status === 'published'"
            >
              批准
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleReview(row.id, 'reject')"
              :disabled="row.status === 'rejected'"
            >
              驳回
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @change="fetchData"
        />
      </div>
    </el-card>
  </div>
</template>
