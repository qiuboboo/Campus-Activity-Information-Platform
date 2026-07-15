<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import { getCalendarEvents, type CalendarEvent } from '@/api/calendar'

function localDateKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function eventDate(event: CalendarEvent) {
  return event.date || event.event_time?.slice(0, 10) || ''
}

const router = useRouter()
const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth())
const selected = ref(localDateKey(now))
const events = ref<CalendarEvent[]>([])
const loading = ref(false)
const error = ref('')
const days = ['日', '一', '二', '三', '四', '五', '六']
const monthKey = computed(() => `${year.value}-${String(month.value + 1).padStart(2, '0')}`)
const cells = computed(() => {
  const first = new Date(year.value, month.value, 1)
  const offset = first.getDay()
  const count = new Date(year.value, month.value + 1, 0).getDate()
  return Array.from({ length: offset + count }, (_, index) => index < offset ? null : new Date(year.value, month.value, index - offset + 1))
})
const selectedEvents = computed(() => events.value.filter((event) => eventDate(event) === selected.value))

async function load() {
  loading.value = true
  error.value = ''
  try { events.value = (await getCalendarEvents(monthKey.value)).data.events } catch (caught: any) { error.value = caught?.response?.data?.message || '日历加载失败' } finally { loading.value = false }
}

function shift(delta: number) {
  const next = new Date(year.value, month.value + delta, 1)
  year.value = next.getFullYear()
  month.value = next.getMonth()
  selected.value = `${year.value}-${String(month.value + 1).padStart(2, '0')}-01`
}

watch(monthKey, load)
onMounted(load)
</script>

<template>
  <AppShell title="我的日历">
    <section class="surface-card calendar-toolbar"><el-button @click="shift(-1)">上月</el-button><strong>{{ year }} 年 {{ month + 1 }} 月</strong><el-button @click="shift(1)">下月</el-button></section>
    <PageState :loading="loading" :error="error" @retry="load">
      <div class="calendar-layout">
        <section class="surface-card calendar"><div v-for="day in days" :key="day" class="weekday">{{ day }}</div><button v-for="(date, index) in cells" :key="index" class="day" :class="{ empty: !date, selected: date && localDateKey(date) === selected, hasEvent: date && events.some((event) => eventDate(event) === localDateKey(date)) }" :disabled="!date" @click="date && (selected = localDateKey(date))">{{ date?.getDate() }}</button></section>
        <aside class="surface-card event-panel"><h2>{{ selected }} 日程</h2><el-empty v-if="!selectedEvents.length" description="当日暂无日程"/><template v-else><button v-for="event in selectedEvents.filter(event => event.activity_id)" :key="event.id || event.title" type="button" class="event event-link" :aria-label="`查看活动：${event.title}`" @click="router.push(`/activity/${event.activity_id}`)"><time>{{ event.time }}</time><div><strong>{{ event.title }}</strong><p>收藏活动</p></div></button><article v-for="event in selectedEvents.filter(event => !event.activity_id)" :key="event.id || event.title" class="event"><time>{{ event.time }}</time><div><strong>{{ event.title }}</strong><p>个人日程</p></div></article></template></aside>
      </div>
    </PageState>
  </AppShell>
</template>

<style scoped>
.calendar-toolbar { padding: 14px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; color: var(--brand-dark); }
.calendar-layout { display: grid; grid-template-columns: minmax(0, 1fr) 310px; gap: 20px; }.calendar { padding: 18px; display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }.weekday { text-align: center; color: var(--text-muted); font-size: 13px; padding: 8px; }.day { min-height: 70px; border: 0; border-radius: 10px; background: #f8fbf9; color: var(--text-main); cursor: pointer; text-align: left; padding: 10px; }.day:hover,.day.selected { background: var(--brand-soft); color: var(--brand-dark); }.day.hasEvent { box-shadow: inset 0 -3px 0 var(--brand-accent); }.day.empty { background: transparent; cursor: default; }.event-panel { padding: 20px; }.event-panel h2 { font-size: 17px; color: var(--brand-dark); margin: 0 0 14px; }.event { border-top: 1px solid var(--line); padding: 14px 0; display: flex; gap: 12px; }.event-link { width: 100%; border-left: 0; border-right: 0; border-bottom: 0; background: transparent; text-align: left; cursor: pointer; }.event-link:hover,.event-link:focus-visible { background: var(--brand-soft); outline: 2px solid var(--brand-accent); outline-offset: 2px; }.event time { font-weight: 700; color: var(--brand-accent); }.event p { font-size: 13px; color: var(--text-muted); margin: 5px 0 0; }@media(max-width:800px){.calendar-layout{grid-template-columns:1fr}.day{min-height:48px}}
</style>
