<script setup lang="ts">
import { Calendar, Location, User, View } from '@element-plus/icons-vue'
import ActivityCover from '@/components/ActivityCover.vue'

interface Props {
  title: string
  summary: string
  eventTime: string | null
  location: string | null
  organizer: string | null
  activityType: string | null
  coverImageUrl?: string | null
  views: number
}

defineProps<Props>()
</script>

<template>
  <section class="activity-header" :class="{ 'activity-header--with-cover': coverImageUrl }">
    <div class="header-content">
      <div class="header-top">
        <el-tag v-if="activityType" type="success" effect="plain" round>{{ activityType }}</el-tag>
        <el-tag v-else type="info" effect="plain" round>活动详情</el-tag>
      </div>

      <h1 class="title">{{ title }}</h1>
      <p class="summary">{{ summary || '暂无摘要' }}</p>

      <div class="meta-row">
        <span><el-icon><Calendar /></el-icon>{{ eventTime || '-' }}</span>
        <span><el-icon><Location /></el-icon>{{ location || '-' }}</span>
        <span><el-icon><User /></el-icon>{{ organizer || '-' }}</span>
        <span><el-icon><View /></el-icon>{{ views }} 次浏览</span>
      </div>
    </div>

    <div class="header-cover">
      <ActivityCover :src="coverImageUrl" :category="activityType" :alt="title" />
    </div>
  </section>
</template>

<style scoped>
.activity-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 24px;
  align-items: stretch;
  background: linear-gradient(135deg, #f7fbf8 0%, #ffffff 100%);
  border: 1px solid #e8f2ea;
  border-radius: 20px;
  padding: 24px 28px;
  box-shadow: 0 8px 30px rgba(13, 94, 60, 0.06);
}

.header-content { min-width: 0; }
.header-top { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.title { margin: 0; font-size: 30px; line-height: 1.25; color: #123b2a; font-weight: 800; }
.summary { margin: 12px 0 0; color: #5f6b66; line-height: 1.8; font-size: 14px; }
.meta-row { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 18px; color: #4b5b54; font-size: 13px; }
.meta-row span { display: inline-flex; align-items: center; gap: 6px; }
.header-cover { min-height: 180px; border-radius: 14px; overflow: hidden; display: grid; font-size: 22px; }
@media (max-width: 820px) {
  .activity-header { grid-template-columns: 1fr; padding: 20px; }
  .header-cover { min-height: 160px; order: -1; }
  .title { font-size: 24px; }
}
</style>
