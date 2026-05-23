<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ActivityHeader from '@/components/activity/ActivityHeader.vue'
import ActivityMeta from '@/components/activity/ActivityMeta.vue'
import ActivityBody from '@/components/activity/ActivityBody.vue'
import { getActivityById, type ActivityDetail as ActivityDetailType } from '@/api/activities'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const detail = ref<ActivityDetailType | null>(null)
const notImplementedMessage = '内容未实现！'

const activityId = computed(() => Number(route.params.id))
const sourceLabel = computed(() => {
  const value = route.query?.source
  return typeof value === 'string' && value.trim() ? value : ''
})
const redirectTarget = computed(() => {
  const value = route.query?.redirect
  return typeof value === 'string' && value.trim() ? value : ''
})

async function fetchDetail() {
  loading.value = true
  try {
    const res = await getActivityById(activityId.value)
    detail.value = res.data || null
    if (!detail.value) {
      ElMessage.error('活动不存在或已下线')
      router.replace('/')
    }
  } catch {
    ElMessage.error('加载活动详情失败')
    router.replace('/')
  } finally {
    loading.value = false
  }
}

function goBack() {
  if (redirectTarget.value) {
    router.replace(redirectTarget.value)
    return
  }

  if (sourceLabel.value) {
    router.push('/')
    return
  }

  router.back()
}

function showNotImplemented() {
  ElMessage.info(notImplementedMessage)
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(fetchDetail)
</script>

<template>
  <div class="detail-page">
    <div class="detail-shell">
      <el-button text class="back-btn" @click="goBack">← 返回</el-button>

      <div v-if="sourceLabel" class="source-hint">
        来源：{{ sourceLabel }}
      </div>

      <el-skeleton v-if="loading" animated :rows="8" />

      <template v-else-if="detail">
        <ActivityHeader
          :title="detail.title"
          :summary="detail.summary"
          :event-time="formatDateTime(detail.event_time)"
          :location="detail.location"
          :organizer="detail.organizer"
          :activity-type="detail.activity_type"
          :views="detail.meta?.views ?? 0"
        />

        <div class="detail-grid">
          <ActivityBody
            :raw-text="detail.raw_text"
            :attachments="detail.attachments || []"
          />

          <ActivityMeta
            :tags="detail.tags || []"
            :registrations="detail.meta?.registrations ?? 0"
            :created-at="formatDateTime(detail.created_at)"
          />
        </div>

        <section class="action-card">
          <div class="action-text">
            <h3>参与这场活动</h3>
            <p>报名、分享、收藏将在下一阶段接入真实接口。当前页面已完成结构与数据联通。</p>
          </div>
          <div class="action-buttons">
            <el-button type="primary" @click="showNotImplemented">立即报名</el-button>
            <el-button @click="showNotImplemented">分享</el-button>
            <el-button @click="showNotImplemented">收藏</el-button>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.detail-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #eef7f1 0%, #f8fbf8 38%, #f5f7f6 100%);
  padding: 32px 20px 48px;
}

.detail-shell {
  max-width: 1180px;
  margin: 0 auto;
}

.back-btn {
  margin-bottom: 16px;
  color: #0d5e3c;
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  margin-top: 18px;
}

.action-card {
  margin-top: 18px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 20px 22px;
  border-radius: 18px;
  background: linear-gradient(135deg, #0d5e3c 0%, #13714a 100%);
  color: #fff;
  box-shadow: 0 18px 40px rgba(13, 94, 60, 0.18);
}

.action-text h3 {
  margin: 0 0 6px;
  font-size: 18px;
}

.action-text p {
  margin: 0;
  opacity: 0.9;
  line-height: 1.7;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 960px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .action-card {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
