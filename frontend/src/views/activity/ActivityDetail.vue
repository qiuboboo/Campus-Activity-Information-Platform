<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import ActivityHeader from '@/components/activity/ActivityHeader.vue'
import ActivityMeta from '@/components/activity/ActivityMeta.vue'
import ActivityBody from '@/components/activity/ActivityBody.vue'
import PosterPreview from '@/components/PosterPreview.vue'
import { cancelRegistration, getActivityById, registerForActivity, setActivityFavorite, type ActivityDetail as ActivityDetailType } from '@/api/activities'
import { getActivityKnowledgeContext, subscribeToKnowledgeNode, type ActivityKnowledgeContext } from '@/api/knowledge'
import { addActivityToCalendar, downloadActivityIcs, removeActivityFromCalendar } from '@/api/calendar'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const loading = ref(true)
const detail = ref<ActivityDetailType | null>(null)
const registering = ref(false)
const favorite = ref(false)
const registered = ref(false)
const inCalendar = ref(false)
const calendarBusy = ref(false)
const context = ref<ActivityKnowledgeContext>({ nodes: [], related: [] })
let requestVersion = 0

const activityId = computed(() => Number(route.params.id))
const sourceLabel = computed(() => {
  const value = route.query?.source
  return typeof value === 'string' && value.trim() ? value : ''
})
const redirectTarget = computed(() => {
  const value = route.query?.redirect
  return typeof value === 'string' && value.trim() ? value : ''
})
const sourceUrl = computed(() => {
  const value = context.value.source?.url || detail.value?.source_url
  if (!value) return ''
  try {
    const url = new URL(value)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : ''
  } catch { return '' }
})

async function fetchDetail() {
  const version = ++requestVersion
  loading.value = true
  detail.value = null
  context.value = { nodes: [], related: [] }
  favorite.value = false
  registered.value = false
  inCalendar.value = false
  try {
    const res = await getActivityById(activityId.value)
    if (version !== requestVersion) return
    detail.value = res.data || null
    favorite.value = Boolean(detail.value?.favorite)
    registered.value = Boolean(detail.value?.registered)
    inCalendar.value = Boolean(detail.value?.in_calendar)
    getActivityKnowledgeContext(activityId.value).then((value) => {
      if (version === requestVersion) context.value = value
    }).catch(() => { /* the detail stays usable without related knowledge */ })
    if (!detail.value) {
      ElMessage.error('活动不存在或已下线')
      router.replace('/')
    }
  } catch {
    if (version === requestVersion) detail.value = null
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

async function toggleRegister() {
  if (!detail.value) return
  if (!auth.isLoggedIn) { router.push({ path: '/auth/login', query: { redirect: route.fullPath } }); return }
  registering.value = true
  try {
    if (registered.value) {
      const { data } = await cancelRegistration(detail.value.id)
      detail.value.meta = { ...(detail.value.meta || { views: 0, registrations: 0 }), registrations: data.registrations }
      registered.value = false
      ElMessage.success('已取消报名')
    } else {
      const { data } = await registerForActivity(detail.value.id)
      detail.value.meta = { ...(detail.value.meta || { views: 0, registrations: 0 }), registrations: data.registrations }
      registered.value = true
      ElMessage.success(data.already_registered ? '你已报名该活动' : '报名成功')
    }
  } catch { /* interceptor handles request errors */ } finally { registering.value = false }
}
async function toggleFavorite() {
  if (!detail.value) return
  if (!auth.isLoggedIn) { router.push({ path: '/auth/login', query: { redirect: route.fullPath } }); return }
  try { const { data } = await setActivityFavorite(detail.value.id, !favorite.value); favorite.value = data.favorite; ElMessage.success(favorite.value ? '已收藏' : '已取消收藏') } catch { /* interceptor handles request errors */ }
}
async function share() {
  const url = window.location.href
  try { if (navigator.share) await navigator.share({ title: detail.value?.title, url }); else { await navigator.clipboard.writeText(url); ElMessage.success('活动链接已复制') } } catch { /* user cancelled or clipboard is unavailable */ }
}
async function toggleCalendar() {
  if (!detail.value) return
  if (!auth.isLoggedIn) { router.push({ path: '/auth/login', query: { redirect: route.fullPath } }); return }
  calendarBusy.value = true
  try {
    if (inCalendar.value) { await removeActivityFromCalendar(detail.value.id); inCalendar.value = false; ElMessage.success('已从我的日历移除') }
    else { const { data } = await addActivityToCalendar(detail.value.id); inCalendar.value = true; ElMessage.success(data.already_added ? '该活动已在我的日历中' : '已加入我的日历') }
  } finally { calendarBusy.value = false }
}
async function exportIcs() {
  if (!detail.value) return
  try {
    const { data } = await downloadActivityIcs(detail.value.id)
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url; link.download = `activity-${detail.value.id}.ics`; link.click()
    URL.revokeObjectURL(url)
  } catch { /* interceptor provides the server error */ }
}
async function subscribe(nodeId: number) {
  if (!auth.isLoggedIn) { router.push({ path: '/auth/login', query: { redirect: route.fullPath } }); return }
  try { await subscribeToKnowledgeNode(nodeId); ElMessage.success('已订阅,相关新活动会通知你,可在个人中心查看') } catch { /* interceptor provides the server error */ }
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

watch(activityId, fetchDetail, { immediate: true })
</script>

<template>
  <AppShell :show-search="false">
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
          :cover-image-url="detail.cover_image_url"
          :views="detail.meta?.views ?? 0"
        />

        <div class="detail-grid">
          <ActivityBody
            :raw-text="detail.raw_text"
            :content-html="detail.content_html"
            :attachments="detail.attachments || []"
          />

          <ActivityMeta
            :tags="detail.tags || []"
            :registrations="detail.meta?.registrations ?? 0"
            :created-at="formatDateTime(detail.created_at)"
          />
        </div>

        <section v-if="context.nodes.length || context.source" class="context-card">
          <div>
            <h2>来源与关联</h2>
            <p v-if="context.source || detail.source_url">活动信息来自
              <a v-if="sourceUrl" :href="sourceUrl" target="_blank" rel="noopener noreferrer">{{ context.source?.name || detail.source_name || '官方来源' }}</a>
              <span v-else>{{ context.source?.name || detail.source_name || '公开来源' }}</span>。
            </p>
          </div>
          <div v-if="context.nodes.length" class="node-list">
            <el-button v-for="node in context.nodes" :key="node.id" size="small" plain @click="subscribe(node.id)">{{ node.name }} · 订阅</el-button>
          </div>
        </section>

        <section v-if="context.related.length" class="related-card">
          <h2>相关活动</h2>
          <div class="related-list">
            <button v-for="item in context.related" :key="item.id" type="button" @click="router.push(`/activity/${item.id}`)"><strong>{{ item.title }}</strong><span>{{ item.reason || '关联推荐' }}</span></button>
          </div>
        </section>

        <section class="action-card">
          <div class="action-text">
            <h3>参与这场活动</h3>
            <p>报名、分享和收藏都将保留清晰反馈；报名需要登录。</p>
          </div>
          <div class="action-buttons">
            <el-button :type="registered ? 'plain' : 'primary'" :loading="registering" @click="toggleRegister">{{ registered ? '取消报名' : '立即报名' }}</el-button>
            <el-button @click="share">分享</el-button>
            <el-button @click="toggleFavorite">{{ favorite ? '取消收藏' : '收藏' }}</el-button>
            <el-button :loading="calendarBusy" @click="toggleCalendar">{{ inCalendar ? '移出日历' : '加入日历' }}</el-button>
            <el-button @click="exportIcs">导出 ICS</el-button>
            <PosterPreview :activity-id="detail.id" :title="detail.title" />
          </div>
        </section>
      </template>
      <el-result v-else icon="error" title="活动不存在或已下线" sub-title="请检查链接，或返回活动列表。"><template #extra><el-button type="primary" @click="router.push('/activities')">浏览活动</el-button></template></el-result>
    </div>
  </div>
  </AppShell>
</template>

<style scoped>
.detail-page {
  min-height: calc(100vh - 60px);
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
.context-card,.related-card { margin-top:18px;padding:20px 22px;border:1px solid #e4efe7;border-radius:18px;background:#fff;box-shadow:0 8px 22px rgba(19,59,42,.05) }
.context-card { display:flex;gap:20px;justify-content:space-between;align-items:center }.context-card h2,.related-card h2{margin:0 0 7px;color:#133b2a;font-size:18px}.context-card p{margin:0;color:#5f6b66}.context-card a{color:var(--brand);font-weight:600}.node-list{display:flex;flex-wrap:wrap;gap:8px}.related-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}.related-list button{border:1px solid #e5eee8;background:#f8fbf9;border-radius:12px;padding:13px;text-align:left;cursor:pointer;color:#133b2a}.related-list button:hover{background:var(--brand-soft)}.related-list span{display:block;margin-top:5px;color:#6b7671;font-size:13px}

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
  .context-card { align-items:flex-start; flex-direction:column; }
}
</style>
