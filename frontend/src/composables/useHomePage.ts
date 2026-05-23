import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import type { Poster } from '@/api/posters'
import { listPosters } from '@/api/posters'
import { getCalendarEvents } from '@/api/calendar'

export function useHomePage() {
  const auth = useAuthStore()
  const router = useRouter()

  const hotPosters = ref<Poster[]>([])
  const recentPosters = ref<Poster[]>([])
  const activityTypeList = ['讲座', '晚会', '竞赛', '论坛', '展览', '招聘', '体育', '其他']
  const loading = ref(true)
  const searchKeyword = ref('')

  // ---- 轮播 ----
  const currentHotIndex = ref(0)
  let hotTimer: ReturnType<typeof setInterval> | null = null

  function startHotCarousel() {
    stopHotCarousel()
    if (hotPosters.value.length < 2) return
    hotTimer = setInterval(() => {
      currentHotIndex.value = (currentHotIndex.value + 1) % hotPosters.value.length
    }, 4000)
  }

  function stopHotCarousel() {
    if (hotTimer) {
      clearInterval(hotTimer)
      hotTimer = null
    }
  }

  // ---- 左侧导航 ----
  const activeNav = ref('all')

  function selectNav(key: string) {
    activeNav.value = key
    if (key === 'create' || key === 'my') {
      if (!auth.isLoggedIn) {
        router.push('/auth/login')
        return
      }
      ElMessage.info('功能建设中')
      return
    }
    const el = document.getElementById(`section-${key}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // ---- 日历 ----
  const today = new Date()
  const currentYear = ref(today.getFullYear())
  const currentMonth = ref(today.getMonth())
  const selectedDate = ref<Date>(new Date())
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']

  const calendarDays = computed(() => {
    const year = currentYear.value
    const month = currentMonth.value
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const startOffset = firstDay.getDay()
    const daysInMonth = lastDay.getDate()

    const days: { date: Date; isCurrentMonth: boolean; isToday: boolean; isSelected: boolean }[] = []

    for (let i = startOffset - 1; i >= 0; i--) {
      const d = new Date(year, month, -i)
      days.push({ date: d, isCurrentMonth: false, isToday: false, isSelected: false })
    }
    for (let i = 1; i <= daysInMonth; i++) {
      const d = new Date(year, month, i)
      const now = new Date()
      days.push({
        date: d,
        isCurrentMonth: true,
        isToday: d.toDateString() === now.toDateString(),
        isSelected: selectedDate.value?.toDateString() === d.toDateString(),
      })
    }
    const remaining = 42 - days.length
    for (let i = 1; i <= remaining; i++) {
      days.push({ date: new Date(year, month + 1, i), isCurrentMonth: false, isToday: false, isSelected: false })
    }
    return days
  })

  function prevMonth() {
    if (currentMonth.value === 0) { currentMonth.value = 11; currentYear.value-- }
    else { currentMonth.value-- }
  }

  function nextMonth() {
    if (currentMonth.value === 11) { currentMonth.value = 0; currentYear.value++ }
    else { currentMonth.value++ }
  }

  function selectDate(date: Date) {
    selectedDate.value = date
  }

  const scheduleItems = ref<{ time: string; title: string; type: string }[]>([])

  async function fetchSchedule() {
    try {
      if (!auth.isLoggedIn) {
        scheduleItems.value = []
        return
      }
      const res = await getCalendarEvents()
      scheduleItems.value = res.data?.events || []
    } catch {
      scheduleItems.value = []
    }
  }

  // ---- 分类筛选 ----
  const selectedCategoryId = ref<string | null>('recent')
  const categoryPosters = ref<Poster[]>([])

  async function fetchCategoryPosters() {
    if (!selectedCategoryId.value || selectedCategoryId.value === 'recent') {
      categoryPosters.value = [...recentPosters.value].sort(
        (a: Poster, b: Poster) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      return
    }
    categoryPosters.value = [...recentPosters.value]
      .filter(p => p.activity_type === selectedCategoryId.value)
      .sort((a: Poster, b: Poster) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  }

  function selectCategory(id: string | null) {
    selectedCategoryId.value = id
    fetchCategoryPosters()
  }

  // ---- 数据获取 ----
  async function fetchData() {
    loading.value = true
    try {
      const [hotRes, recentRes] = await Promise.all([
        listPosters({ status: 'published', per_page: 6 }),
        listPosters({ per_page: 6 }),
      ])
      hotPosters.value = (hotRes.data?.items || []).sort(
        (a: Poster, b: Poster) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      recentPosters.value = (recentRes.data?.items || []).sort(
        (a: Poster, b: Poster) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      categoryPosters.value = recentPosters.value
    } catch { /* handled by interceptor */ }
    finally { loading.value = false }
  }

  // ---- 工具 ----
  function formatTime(iso: string | null) {
    if (!iso) return '-'
    return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }

  function formatDate(iso: string | null) {
    if (!iso) return '-'
    return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
  }

  function goPosterDetail(id: number) {
    ElMessage.info('功能建设中')
  }

  function handleSearch() {
    const q = searchKeyword.value.trim()
    if (q) ElMessage.info('搜索功能建设中')
  }

  function handleLogout() { auth.logout(); router.push('/') }

  const currentYearLabel = new Date().getFullYear()

  watch(hotPosters, (val) => {
    currentHotIndex.value = 0
    if (val.length > 0) startHotCarousel()
    else stopHotCarousel()
  })
  onMounted(() => {
    fetchData()
    fetchSchedule()
  })
  onUnmounted(stopHotCarousel)

  return {
    auth, router,
    hotPosters, recentPosters, activityTypeList, loading, searchKeyword,
    currentHotIndex, startHotCarousel, stopHotCarousel,
    activeNav, selectNav,
    currentYear, currentMonth, selectedDate, weekDays,
    calendarDays, prevMonth, nextMonth, selectDate, scheduleItems,
    selectedCategoryId, categoryPosters, fetchCategoryPosters, selectCategory,
    fetchData, fetchSchedule, formatTime, formatDate, goPosterDetail, handleSearch, handleLogout, currentYearLabel,
  }
}
