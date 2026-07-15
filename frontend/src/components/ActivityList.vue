<script setup lang="ts">
import { Calendar, Location, User } from '@element-plus/icons-vue'
import type { Activity } from '@/api/activities'
import { useRouter } from 'vue-router'
import ActivityCover from '@/components/ActivityCover.vue'

defineProps<{ activities: Activity[] }>()
const router = useRouter()
const formatTime = (value: string | null) => value ? new Date(value).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '时间待定'
</script>

<template>
  <div class="activity-list">
    <article
      v-for="activity in activities"
      :key="activity.id"
      class="activity-card"
      tabindex="0"
      role="link"
      :aria-label="`查看活动：${activity.title}`"
      @click="router.push(`/activity/${activity.id}`)"
      @keyup.enter="router.push(`/activity/${activity.id}`)"
      @keydown.space.prevent="router.push(`/activity/${activity.id}`)"
    >
      <div class="activity-cover">
        <ActivityCover :src="activity.cover_image_url" :category="activity.activity_type" :alt="activity.title" />
      </div>
      <div class="activity-card__main">
        <div class="activity-card__top">
          <el-tag size="small" type="success" effect="plain">{{ activity.activity_type || '活动' }}</el-tag>
          <el-tag v-if="activity.status !== 'published'" size="small" type="warning">{{ activity.status }}</el-tag>
        </div>
        <h2>{{ activity.title }}</h2>
        <p>{{ activity.summary || activity.raw_text }}</p>
        <div class="activity-card__meta">
          <span><el-icon><Calendar /></el-icon>{{ formatTime(activity.event_time) }}</span>
          <span><el-icon><Location /></el-icon>{{ activity.location || '地点待定' }}</span>
          <span><el-icon><User /></el-icon>{{ activity.organizer || '主办方待定' }}</span>
        </div>
      </div>
      <el-button text type="primary" @click.stop="router.push(`/activity/${activity.id}`)">查看详情</el-button>
    </article>
  </div>
</template>

<style scoped>
.activity-list { display: grid; gap: 14px; }
.activity-card { padding: 18px 20px; display: flex; gap: 18px; align-items: center; justify-content: space-between; background: #fff; border: 1px solid var(--line); border-radius: var(--radius-card); box-shadow: var(--shadow-card); cursor: pointer; transition: transform .2s, box-shadow .2s; }
.activity-card:hover { transform: translateY(-2px); box-shadow: 0 12px 28px rgb(19 59 42 / 11%); }
.activity-cover { width: 120px; height: 86px; flex: 0 0 120px; border-radius: 8px; overflow: hidden; }
.activity-card__main { min-width: 0; flex: 1; }
.activity-card__top { display: flex; gap: 6px; margin-bottom: 8px; }
h2 { margin: 0; color: var(--brand-dark); font-size: 17px; }
p { color: var(--text-muted); line-height: 1.7; margin: 8px 0; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.activity-card__meta { display: flex; gap: 14px; flex-wrap: wrap; color: var(--text-muted); font-size: 13px; }
.activity-card__meta span { display: inline-flex; gap: 4px; align-items: center; }
@media (max-width: 600px) { .activity-card { align-items: flex-start; flex-direction: column; gap: 8px; } .activity-cover { width: 100%; height: 120px; flex-basis: auto; } }
</style>
