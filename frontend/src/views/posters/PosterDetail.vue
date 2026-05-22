<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPoster, getRelated, submitPoster, type Poster } from '@/api/posters'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const poster = ref<Poster | null>(null)
const related = ref<any>(null)
const loading = ref(true)
const submitting = ref(false)

async function fetchData() {
  try {
    const id = Number(route.params.id)
    const [posterRes, relatedRes] = await Promise.all([
      getPoster(id),
      getRelated(id),
    ])
    poster.value = posterRes.data.item
    related.value = relatedRes.data
  } catch {
    router.push('/posters')
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!poster.value) return
  try {
    await ElMessageBox.confirm(
      '提交后海报将进入审核队列，等待管理员审核。确定提交？',
      '提交审核',
      { confirmButtonText: '确定提交', cancelButtonText: '取消', type: 'info' },
    )
    submitting.value = true
    await submitPoster(poster.value.id)
    ElMessage.success('已提交审核')
    fetchData()
  } catch {
    // cancelled or error
  } finally {
    submitting.value = false
  }
}

function goEdit() {
  if (poster.value) {
    router.push(`/posters/${poster.value.id}/edit`)
  }
}

function formatTime(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  published: { label: '已发布', type: 'success' },
  rejected: { label: '已拒绝', type: 'danger' },
}

onMounted(fetchData)
</script>

<template>
  <div v-loading="loading">
    <el-button text type="primary" @click="router.push('/posters')" style="margin-bottom: 12px;">
      <el-icon><ArrowLeft /></el-icon> 返回列表
    </el-button>

    <el-card v-if="poster" shadow="hover" style="border-radius: 8px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div>
            <span style="font-size: 20px; font-weight: bold; color: #303133;">{{ poster.title }}</span>
            <el-tag
              :type="statusMap[poster.status]?.type as any || 'info'"
              size="small"
              style="margin-left: 12px;"
            >
              {{ statusMap[poster.status]?.label || poster.status }}
            </el-tag>
          </div>
          <div style="display: flex; gap: 8px;">
            <!-- 编辑（创建者或管理员） -->
            <el-button
              v-if="auth.isAdmin || auth.user?.id === poster.created_by"
              size="small"
              @click="goEdit"
            >
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <!-- 提交审核（草稿/已拒绝状态下可提交） -->
            <el-button
              v-if="(poster.status === 'draft' || poster.status === 'rejected') && auth.isPublisher"
              size="small"
              type="warning"
              :loading="submitting"
              @click="handleSubmit"
            >
              <el-icon><Upload /></el-icon> 提交审核
            </el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="活动时间" :span="1">
          {{ formatTime(poster.event_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="活动地点" :span="1">
          {{ poster.location || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="主办方" :span="1">
          {{ poster.organizer || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="来源类型" :span="1">
          {{ poster.source_type }}
        </el-descriptions-item>
        <el-descriptions-item label="活动类型" :span="1">
          {{ poster.activity_type || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="质量评分" :span="1">
          <el-tag v-if="poster.quality_score != null" size="small">{{ poster.quality_score }}</el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="来源链接" :span="2">
          <span v-if="poster.source_url">{{ poster.source_url }}</span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="标签" :span="2">
          <span v-if="poster.tags">{{ poster.tags }}</span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="摘要" :span="2">
          {{ poster.summary || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="1">
          {{ formatTime(poster.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间" :span="1">
          {{ formatTime(poster.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- HTML 内容预览 -->
      <div v-if="poster.content_html" style="margin-top: 24px;">
        <h4 style="margin-bottom: 12px; color: #303133;">海报预览</h4>
        <div class="poster-preview" v-html="poster.content_html"></div>
      </div>

      <!-- 知识关联 -->
      <div v-if="related" style="margin-top: 24px;">
        <h4 style="margin-bottom: 12px; color: #303133;">知识关联</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 12px;">
          <el-tag
            v-for="node in related.knowledge_nodes"
            :key="node.id"
            :type="
              node.node?.node_type === 'time' ? 'success' :
              node.node?.node_type === 'place' ? 'primary' :
              node.node?.node_type === 'organization' ? 'warning' :
              node.node?.node_type === 'topic' ? 'danger' : 'info'
            "
            effect="plain"
            style="cursor: pointer;"
          >
            {{ node.node?.name }} ({{ node.node?.node_type }})
          </el-tag>
        </div>
      </div>
    </el-card>

    <el-empty v-else-if="!loading" description="海报不存在" />
  </div>
</template>

<style scoped>
.poster-preview {
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}
.poster-preview :deep(.activity-poster) {
  font-family: inherit;
}
.poster-preview :deep(.poster-title) {
  font-size: 18px;
  margin-bottom: 12px;
  color: #303133;
}
.poster-preview :deep(p) {
  margin: 6px 0;
  color: #606266;
  line-height: 1.6;
}
</style>
