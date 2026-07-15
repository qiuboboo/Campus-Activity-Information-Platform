<template>
  <div class="side-card">
    <div class="side-card-header">
      <el-icon><Calendar /></el-icon>
      <span>{{ currentYear }}年{{ currentMonth + 1 }}月</span>
      <div class="cal-nav">
        <el-button text size="small" @click="$emit('prevMonth')">&lt;</el-button>
        <el-button text size="small" @click="$emit('nextMonth')">&gt;</el-button>
      </div>
    </div>

    <div class="cal-grid">
      <div v-for="wd in weekDays" :key="wd" class="cal-cell cal-weekday">{{ wd }}</div>
      <button
        v-for="(day, idx) in calendarDays"
        :key="idx"
        type="button"
        :disabled="!day.isCurrentMonth"
        :aria-label="`${day.date.getFullYear()}年${day.date.getMonth() + 1}月${day.date.getDate()}日${day.isCurrentMonth ? '' : '，非当前月份'}`"
        class="cal-cell cal-day"
        :class="{
          'cal-other': !day.isCurrentMonth,
          'cal-today': day.isToday,
          'cal-selected': day.isSelected,
        }"
        @click="$emit('selectDate', day.date)"
      >
        {{ day.date.getDate() }}
      </button>
    </div>
  </div>

  <div class="side-card">
    <div class="side-card-header">
      <el-icon><Sunny /></el-icon>
      <span>{{ selectedDate.toLocaleDateString('zh-CN') }} 日程</span>
    </div>
    <div v-if="scheduleError" class="schedule-error"><el-alert type="error" :title="scheduleError" :closable="false" show-icon><template #default><el-button text type="primary" @click="$emit('retrySchedule')">重试</el-button></template></el-alert></div>
    <div class="schedule-list" v-else-if="scheduleItems.length > 0">
      <div v-for="(s, idx) in scheduleItems" :key="idx" class="schedule-item">
        <div class="schedule-time">{{ s.time }}</div>
        <div class="schedule-dot" :class="`dot-${s.type}`"></div>
        <div class="schedule-title">{{ s.title }}</div>
      </div>
    </div>
    <div v-else class="schedule-empty">
      <el-empty :image-size="48" description="暂无日程" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Calendar, Sunny } from '@element-plus/icons-vue'

defineProps<{
  currentYear: number
  currentMonth: number
  weekDays: string[]
  calendarDays: { date: Date; isCurrentMonth: boolean; isToday: boolean; isSelected: boolean }[]
  selectedDate: Date
  scheduleItems: { time: string; title: string; type: string; activity_id?: number }[]
  scheduleError?: string
}>()

defineEmits<{
  (e: 'prevMonth'): void
  (e: 'nextMonth'): void
  (e: 'selectDate', date: Date): void
  (e: 'retrySchedule'): void
}>()
</script>

<style scoped>
.side-card {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04);
}

.side-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #0d5e3c;
  margin-bottom: 12px;
  justify-content: space-between;
}

.cal-nav {
  display: flex;
  gap: 4px;
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  text-align: center;
}

.cal-cell {
  padding: 6px 0;
  font-size: 13px;
  border-radius: 8px;
  border: 0;
  background: transparent;
}

.cal-weekday {
  font-weight: 600;
  color: #909399;
  font-size: 12px;
}

.cal-day {
  cursor: pointer;
  color: #303133;
  transition: all 0.15s;
}

.cal-day:hover {
  background: #f0f9f4;
  color: #0d5e3c;
}

.cal-other {
  color: #d0d0d0;
  cursor: default;
}

.cal-today {
  background: #27a66b !important;
  color: #fff !important;
  font-weight: 700;
}

.cal-selected {
  background: #e8f5e9 !important;
  color: #0d5e3c !important;
  font-weight: 700;
  outline: 2px solid #27a66b;
  outline-offset: -2px;
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.schedule-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}

.schedule-item:last-child { border-bottom: none; }

.schedule-time {
  font-size: 12px;
  font-weight: 600;
  color: #27a66b;
  white-space: nowrap;
  width: 40px;
}

.schedule-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.schedule-dot.dot-info { background: #27a66b; }
.schedule-dot.dot-warning { background: #e6a23c; }

.schedule-title {
  font-size: 13px;
  color: #606266;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.schedule-empty {
  padding: 12px 0;
}
.schedule-error { padding: 4px 0; }
</style>
