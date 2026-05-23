<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { Poster } from '@/api/posters'
import { listPosters } from '@/api/posters'
import {
  Search,
  TrendCharts,
  Collection,
  Clock,
  Calendar,
  Location,
  User,
  ArrowRight,
  School,
  Grid,
  Plus,
  Star,
  Sunny,
} from '@element-plus/icons-vue'

const auth = useAuthStore()
const router = useRouter()

// ==================== 状态 ====================
const hotPosters = ref<Poster[]>([])
const recentPosters = ref<Poster[]>([])
const activityTypeList = ['讲座', '晚会', '竞赛', '论坛', '展览', '招聘', '体育', '其他']
const loading = ref(true)
const searchKeyword = ref('')

// ==================== 热门活动轮播 ====================
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

// ==================== 左侧导航 ====================
const activeNav = ref('all')
const navItems = [
  { key: 'all', label: '全部活动', icon: Grid },
  { key: 'hot', label: '热门推荐', icon: TrendCharts },
  { key: 'categories', label: '按类别', icon: Collection },
  { key: 'my', label: '我的活动', icon: Star },
  { key: 'create', label: '创建活动', icon: Plus },
]

// ==================== 日历状态 ====================
const today = new Date()
const currentYear = ref(today.getFullYear())
const currentMonth = ref(today.getMonth()) // 0-based
const selectedDate = ref<Date | null>(null)
const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startOffset = firstDay.getDay()
  const daysInMonth = lastDay.getDate()

  const days: { date: Date; isCurrentMonth: boolean; isToday: boolean; isSelected: boolean }[] = []

  // 上月补全
  for (let i = startOffset - 1; i >= 0; i--) {
    const d = new Date(year, month, -i)
    days.push({ date: d, isCurrentMonth: false, isToday: false, isSelected: false })
  }

  // 本月
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

  // 下月补全（补满6行=42格）
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const d = new Date(year, month + 1, i)
    days.push({ date: d, isCurrentMonth: false, isToday: false, isSelected: false })
  }

  return days
})

function prevMonth() {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

function selectDate(date: Date) {
  selectedDate.value = date
  // 联动：筛选该日的热门活动显示
}

// ==================== 日程（模拟） ====================
const scheduleItems = computed(() => {
  if (!selectedDate.value) return []
  // 模拟日程数据
  const dayStr = selectedDate.value.toLocaleDateString('zh-CN')
  return [
    { time: '09:00', title: `活动预览 · ${dayStr}`, type: 'info' as const },
    { time: '14:00', title: '待办事项检查', type: 'warning' as const },
  ]
})

// ==================== 类别筛选 ====================
const selectedCategoryId = ref<string | null>('recent')
const categoryPosters = ref<Poster[]>([])

async function fetchCategoryPosters() {
  if (!selectedCategoryId.value || selectedCategoryId.value === 'recent') {
    categoryPosters.value = [...recentPosters.value].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    return
  }
  categoryPosters.value = [...recentPosters.value]
    .filter(p => p.activity_type === selectedCategoryId.value)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

function selectCategory(id: string | null) {
  selectedCategoryId.value = id
  fetchCategoryPosters()
}

// ==================== 数据获取 ====================
async function fetchData() {
  loading.value = true
  try {
    const [hotRes, recentRes] = await Promise.all([
      listPosters({ status: 'published', per_page: 6 }),
      listPosters({ per_page: 6 }),
    ])
    hotPosters.value = (hotRes.data?.items || []).sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    recentPosters.value = (recentRes.data?.items || []).sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    categoryPosters.value = recentPosters.value
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

// ==================== 导航切换 ====================
function selectNav(key: string) {
  activeNav.value = key
  if (key === 'create') {
    if (auth.isLoggedIn) {
      router.push('/dashboard')
    } else {
      router.push('/auth/login')
    }
    return
  }
  if (key === 'my') {
    if (auth.isLoggedIn) {
      router.push('/dashboard')
    } else {
      router.push('/auth/login')
    }
    return
  }
  // 其它导航在当前页通过滚动到对应区块处理
  const el = document.getElementById(`section-${key}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// ==================== 工具函数 ====================
function formatTime(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDate(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function goPosterDetail(id: number) {
  router.push(`/posters/${id}`)
}

function handleSearch() {
  const q = searchKeyword.value.trim()
  if (q) {
    router.push({ path: '/search', query: { q } })
  }
}

function handleLogout() {
  auth.logout()
  router.push('/')
}

const currentYearLabel = new Date().getFullYear()

onMounted(fetchData)

watch(hotPosters, (val) => {
  currentHotIndex.value = 0
  if (val.length > 0) startHotCarousel()
  else stopHotCarousel()
})

onUnmounted(stopHotCarousel)
</script>

<template>
  <div class="home-page">
    <!-- ==================== 顶部导航栏 ==================== -->
    <nav class="home-nav">
      <div class="nav-inner">
        <div class="nav-brand" @click="router.push('/')">
          <span class="nav-brand-title">逸仙活动云</span>
        </div>
        <div class="nav-search">
          <el-input
            v-model="searchKeyword"
            size="large"
            class="nav-search-input"
            placeholder="搜索活动、主题、地点…"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon class="search-prefix-icon"><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="nav-actions">
          <template v-if="auth.isLoggedIn">
            <span class="nav-user">{{ auth.user?.username }}</span>
            <el-button text class="nav-link-text" @click="handleLogout">退出登录</el-button>
          </template>
          <template v-else>
            <el-button text class="nav-link-text" @click="router.push('/auth/login')">登录</el-button>
            <el-button type="primary" class="nav-cta" @click="router.push('/auth/register')">免费注册</el-button>
          </template>
        </div>
      </div>
    </nav>

    <!-- ====== 三栏主体 ====== -->
    <div class="home-body">
      <!-- ====== 左侧导航栏 ====== -->
      <aside class="side-left">
        <nav class="side-nav">
          <div
            v-for="item in navItems"
            :key="item.key"
            class="side-nav-item"
            :class="{ active: activeNav === item.key }"
            @click="selectNav(item.key)"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </div>
        </nav>
        <!-- 分类快捷入口 -->
        <div class="side-divider"></div>
        <div class="side-section-title">分类入口</div>
        <div class="side-categories">
          <div
            v-for="cat in activityTypeList.slice(0, 6)"
            :key="cat"
            class="side-cat-item"
            :class="{ active: selectedCategoryId === cat }"
            @click="selectCategory(cat)"
          >
            <span class="side-cat-dot"></span>
            <span>{{ cat }}</span>
          </div>
        </div>
      </aside>

      <!-- ====== 中间主内容 ====== -->
      <main class="home-main">
        <!-- 热门活动 - 轮播 -->
        <div class="hot-section" v-if="!loading">
          <div class="section-header">
            <h2 class="section-title">
              <el-icon class="section-title-icon"><TrendCharts /></el-icon>
              热门活动
            </h2>
            <el-button text class="section-more" @click="router.push('/posters')">
              查看全部 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
          <div v-if="hotPosters.length > 0" class="hot-carousel" @click="goPosterDetail(hotPosters[currentHotIndex].id)">
            <div class="hc-card">
              <div class="hc-badge">
                <el-tag
                  :type="hotPosters[currentHotIndex].activity_type ? 'success' : 'info'"
                  size="small"
                  effect="plain"
                  round
                >
                  {{ hotPosters[currentHotIndex].activity_type || '活动' }}
                </el-tag>
              </div>
              <h3 class="hc-title">{{ hotPosters[currentHotIndex].title }}</h3>
              <p class="hc-summary">
                {{ hotPosters[currentHotIndex].summary || hotPosters[currentHotIndex].raw_text?.substring(0, 80) || '暂无简介' }}
              </p>
              <div class="hc-meta">
                <span><el-icon size="14"><User /></el-icon> {{ hotPosters[currentHotIndex].organizer || '未知' }}</span>
                <span><el-icon size="14"><Clock /></el-icon> {{ formatTime(hotPosters[currentHotIndex].event_time) }}</span>
                <span><el-icon size="14"><Location /></el-icon> {{ hotPosters[currentHotIndex].location || '待定' }}</span>
              </div>
            </div>
            <!-- 指示点 -->
            <div class="hc-dots" v-if="hotPosters.length > 1">
              <span
                v-for="(_, i) in hotPosters"
                :key="i"
                class="hc-dot"
                :class="{ active: i === currentHotIndex }"
                @click.stop="currentHotIndex = i; startHotCarousel()"
              ></span>
            </div>
          </div>
          <div v-else class="hot-empty">
            <el-empty :image-size="80" description="暂无活动" />
          </div>
        </div>

        <!-- 分类活动 - 滚动区域 -->
        <div class="category-scroll" v-loading="loading">
          <template v-if="loading">
            <section class="content-section">
              <div class="skeleton-title"></div>
              <div class="skeleton-scroll">
                <div v-for="i in 4" :key="i" class="skeleton-card-scroll"></div>
              </div>
            </section>
            <section class="content-section">
              <div class="skeleton-title"></div>
              <div class="skeleton-grid">
                <div v-for="i in 4" :key="i" class="skeleton-card"></div>
              </div>
            </section>
          </template>
          <template v-else>
            <!-- 按类别分区的活动列表 -->
            <section class="content-section" id="section-categories">
              <!-- 类别标签 - 固定 -->
              <div class="section-header">
                <h2 class="section-title">
                  <el-icon class="section-title-icon"><Collection /></el-icon>
                  活动分类
                </h2>
              </div>
              <div class="category-tabs">
                <el-radio-group v-model="selectedCategoryId" @change="fetchCategoryPosters">
                  <el-radio-button value="recent">最近</el-radio-button>
                  <el-radio-button
                    v-for="cat in activityTypeList"
                    :key="cat"
                    :value="cat"
                  >
                    {{ cat }}
                  </el-radio-button>
                </el-radio-group>
              </div>
            </section>
            <!-- 活动列表 - 可滚动 -->
            <div class="cat-scroll-body">
              <div class="cat-poster-list" v-if="categoryPosters.length > 0">
                <div
                  v-for="p in categoryPosters"
                  :key="p.id"
                  class="cat-poster-item"
                  @click="goPosterDetail(p.id)"
                >
                  <div class="cpi-left">
                    <div class="cpi-title">{{ p.title }}</div>
                    <div class="cpi-meta">
                      <span><el-icon size="12"><Location /></el-icon> {{ p.location || '待定' }}</span>
                      <span><el-icon size="12"><Calendar /></el-icon> {{ formatTime(p.event_time) }}</span>
                    </div>
                  </div>
                  <div class="cpi-tag">
                    <el-tag size="small" type="success" effect="plain" round>
                      {{ p.activity_type || '活动' }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <div v-else class="cat-poster-empty">
                <el-empty :image-size="80" description="该类别暂无活动" />
              </div>
            </div>

            <!-- 空状态 -->
            <section class="content-section" v-if="hotPosters.length === 0 && recentPosters.length === 0">
              <div class="empty-state">
                <el-empty description="暂无活动数据，请稍后再来">
                  <el-button type="primary" @click="fetchData">刷新</el-button>
                </el-empty>
              </div>
            </section>
          </template>
        </div>
      </main>

      <!-- ====== 右侧辅助栏 ====== -->
      <aside class="side-right">
        <!-- 日历 -->
        <div class="side-card">
          <div class="side-card-header">
            <el-icon><Calendar /></el-icon>
            <span>{{ currentYear }}年{{ currentMonth + 1 }}月</span>
            <div class="cal-nav">
              <el-button text size="small" @click="prevMonth">&lt;</el-button>
              <el-button text size="small" @click="nextMonth">&gt;</el-button>
            </div>
          </div>
          <div class="cal-grid">
            <div v-for="wd in weekDays" :key="wd" class="cal-cell cal-weekday">{{ wd }}</div>
            <div
              v-for="(day, idx) in calendarDays"
              :key="idx"
              class="cal-cell cal-day"
              :class="{
                'cal-other': !day.isCurrentMonth,
                'cal-today': day.isToday,
                'cal-selected': day.isSelected,
              }"
              @click="selectDate(day.date)"
            >
              {{ day.date.getDate() }}
            </div>
          </div>
        </div>

        <!-- 日程 -->
        <div class="side-card">
          <div class="side-card-header">
            <el-icon><Sunny /></el-icon>
            <span>{{ selectedDate ? selectedDate.toLocaleDateString('zh-CN') : '请选择日期' }} 日程</span>
          </div>
          <div class="schedule-list" v-if="scheduleItems.length > 0">
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
      </aside>
    </div>

    <!-- ==================== 页脚 ==================== -->
    <footer class="home-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <div class="nav-logo footer-logo">
            <el-icon size="18"><School /></el-icon>
          </div>
          <span class="footer-name">逸仙活动云</span>
        </div>
        <div class="footer-links">
          <span @click="router.push('/posters')">浏览活动</span>
          <span @click="router.push('/knowledge')">知识图谱</span>
          <span @click="router.push('/search')">搜索</span>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© {{ currentYearLabel }} 中山大学 · 校园活动信息平台</p>
      </div>
    </footer>

    <!-- 回到顶部 -->
    <el-backtop :visibility-height="400" :right="32" :bottom="40" />
  </div>
</template>

<style scoped>
/* ====== 页面容器 ====== */
.home-page {
  position: relative;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  text-align: left;
  overflow: hidden;
}

/* ====== 导航栏 ====== */
.home-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #0d5e3c;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-inner {
  max-width: 1400px;
  margin: 0 auto;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
}

.nav-brand {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: calc(160px + 28px - 32px);
}

.nav-brand-title {
  font-size: 28px;
  font-weight: 800;
  color: #fff;
  letter-spacing: 1px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-search {
  flex: 1;
  max-width: 360px;
  margin: 0 24px;
}

.nav-search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  box-shadow: none;
  padding: 4px 16px;
  transition: background 0.2s;
}

.nav-search-input :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.25);
}

.nav-search-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.3);
}

.nav-search-input :deep(.el-input__inner) {
  color: #fff;
  font-size: 16px;
}

.nav-search-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}

.nav-search-input :deep(.el-input__prefix) {
  color: rgba(255, 255, 255, 0.5);
}

.nav-cta {
  background: #27a66b !important;
  border: none !important;
  font-weight: 600;
  border-radius: 20px;
  padding: 18px 24px;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(39, 166, 107, 0.25);
  transition: all 0.3s;
}

.nav-cta:hover {
  background: #1f8d59 !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(39, 166, 107, 0.35);
}

.nav-user {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-dashboard-btn {
  background: rgba(255, 255, 255, 0.12) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
  font-weight: 600;
  border-radius: 20px;
  padding: 18px 20px;
  transition: all 0.3s;
}

.nav-dashboard-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.35) !important;
  transform: translateY(-1px);
}

.nav-link-text {
  color: rgba(255, 255, 255, 0.85) !important;
  font-size: 15px;
  font-weight: 500;
  padding: 18px 16px;
  transition: color 0.2s;
}

.nav-link-text:hover {
  color: #fff !important;
}

.nav-logo {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.search-prefix-icon {
  font-size: 16px;
}

/* ====== 三栏主体布局 ====== */
.home-body {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 0 32px 0 188px;
  display: flex;
  gap: 28px;
  overflow: hidden;
  min-height: 0;
}

/* ====== 左侧导航栏 ====== */
.side-left {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 160px;
  background: #f0f9f4;
  overflow-y: auto;
  padding-top: 104px;
  z-index: 1;
  border-right: 1px solid #d0ede0;
}

.side-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 8px;
}

.side-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  transition: all 0.2s;
}

.side-nav-item:hover {
  background: #f0f9f4;
  color: #0d5e3c;
}

.side-nav-item.active {
  background: #e8f5e9;
  color: #0d5e3c;
  font-weight: 700;
}

.side-nav-item .el-icon {
  font-size: 18px;
}

.side-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 12px 16px;
}

.side-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #b0b0b0;
  padding: 0 16px 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.side-categories {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 8px;
}

.side-cat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: all 0.2s;
}

.side-cat-item:hover {
  background: #f0f9f4;
  color: #0d5e3c;
}

.side-cat-item.active {
  background: #e8f5e9;
  color: #0d5e3c;
  font-weight: 600;
}

.side-cat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #27a66b;
}

/* ====== 中间主内容 ====== */
.home-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 热门活动 - 固定区域 */
.hot-section {
  flex-shrink: 0;
}

/* 分类活动 - 滚动区域 */
.category-scroll {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  margin-top: 8px;
}

.cat-scroll-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.cat-scroll-body::-webkit-scrollbar {
  width: 4px;
}

.cat-scroll-body::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 2px;
}

.content-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  font-size: 20px;
  font-weight: 800;
  color: #0d5e3c;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title-icon {
  font-size: 20px;
  color: #27a66b;
}

.section-more {
  color: #0b7d5b !important;
  font-size: 13px;
  transition: color 0.2s;
}

.section-more:hover {
  color: #0ea36f !important;
  background: rgba(11, 125, 91, 0.06) !important;
}

/* ====== 卡片入场动画 ====== */
@keyframes card-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.hot-carousel,
.cat-poster-item {
  animation: card-in 0.5s ease-out both;
}
.hot-carousel { animation-delay: 0s; }

.cat-poster-item:nth-child(1) { animation-delay: 0.05s; }
.cat-poster-item:nth-child(2) { animation-delay: 0.1s; }
.cat-poster-item:nth-child(3) { animation-delay: 0.15s; }
.cat-poster-item:nth-child(4) { animation-delay: 0.2s; }
.cat-poster-item:nth-child(5) { animation-delay: 0.25s; }
.cat-poster-item:nth-child(6) { animation-delay: 0.3s; }

/* ====== 骨架屏 ====== */
.skeleton-title {
  height: 24px;
  width: 140px;
  background: linear-gradient(90deg, #e8e8e8 25%, #f5f5f5 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: 6px;
  margin-bottom: 16px;
}

.skeleton-scroll {
  display: flex;
  gap: 16px;
  overflow: hidden;
}

.skeleton-card-scroll {
  width: 240px;
  height: 160px;
  background: linear-gradient(90deg, #e8e8e8 25%, #f5f5f5 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: 16px;
  flex-shrink: 0;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.skeleton-card {
  height: 100px;
  background: linear-gradient(90deg, #e8e8e8 25%, #f5f5f5 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: 12px;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ====== 热门活动 - 轮播 ====== */
.hot-carousel {
  background: #fff;
  border-radius: 14px;
  padding: 28px 32px 20px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04);
  border-left: 4px solid #27a66b;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  position: relative;
}

.hot-carousel:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(13, 94, 60, 0.08);
}

.hot-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  background: #fff;
  border: 1px dashed #d8dee9;
  border-radius: 14px;
}

.hc-badge { margin-bottom: 12px; }

.hc-title {
  font-size: 20px;
  font-weight: 800;
  color: #0d5e3c;
  margin: 0 0 10px;
}

.hc-summary {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0 0 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hc-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #909399;
  flex-wrap: wrap;
}

.hc-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 指示点 */
.hc-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}

.hc-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d0d0d0;
  cursor: pointer;
  transition: all 0.25s;
}

.hc-dot.active {
  background: #27a66b;
  width: 24px;
  border-radius: 4px;
}

.hc-dot:hover {
  background: #27a66b;
}

/* ====== 活动分类标签 + 列表 ====== */
.category-tabs {
  margin-bottom: 8px;
  overflow-x: auto;
  white-space: nowrap;
  padding-bottom: 4px;
}

.category-tabs :deep(.el-radio-group) {
  display: inline-flex;
  gap: 0;
  flex-wrap: nowrap;
}

.category-tabs :deep(.el-radio-button__inner) {
  font-size: 13px;
  padding: 8px 16px;
  border-color: #e8e8e8;
}

.cat-poster-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cat-poster-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

.cat-poster-item:hover {
  background: #f5fcf8;
  transform: translateX(4px);
}

.cpi-left { flex: 1; min-width: 0; }

.cpi-title {
  font-size: 14px;
  font-weight: 600;
  color: #0d5e3c;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cpi-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 16px;
}

.cpi-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cpi-tag { flex-shrink: 0; margin-left: 12px; }

.cat-poster-empty {
  padding: 24px 0;
}

/* ====== 空状态 ====== */
.empty-state {
  background: #fff;
  border-radius: 14px;
  padding: 40px 0;
}

/* ====== 右侧辅助栏 ====== */
.side-right {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

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
  pointer-events: none;
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

/* ====== 日程 ====== */
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

/* ====== 页脚 ====== */
.home-footer {
  background: #0a0a0a;
  flex-shrink: 0;
  padding: 0;
  position: relative;
  z-index: 2;
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 10px 32px 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-logo { width: 24px; height: 24px; border-radius: 6px; }

.footer-name {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.footer-links { display: flex; gap: 20px; }

.footer-links span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  cursor: pointer;
  transition: color 0.2s;
}

.footer-links span:hover { color: #27a66b; }

.footer-bottom {
  max-width: 1400px;
  margin: 0 auto;
  padding: 6px 32px 10px;
  text-align: center;
}

.footer-bottom p {
  margin: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  line-height: 1.6;
}

/* ====== 响应式 ====== */
@media (max-width: 1024px) {
  .side-right { display: none; }
  .home-body { gap: 20px; }
}

@media (max-width: 768px) {
  .side-left { display: none; }
  .home-body { padding: 16px 16px 0; flex-direction: column; }
  .nav-search { display: none; }
  .nav-brand-title { font-size: 22px; }
  .nav-inner { padding: 0 16px; }
  .section-title { font-size: 17px; }
  .hc-summary { font-size: 13px; }
  .footer-inner { flex-direction: column; gap: 8px; padding: 10px 16px 6px; }
  .footer-bottom { padding: 4px 16px 8px; }
}

@media (max-width: 480px) {
  .nav-inner { padding: 0 12px; }
  .home-body { padding: 12px; }
  .category-tabs :deep(.el-radio-button__inner) { padding: 6px 12px; font-size: 12px; }
  .cat-poster-item { padding: 12px 16px; flex-direction: column; align-items: flex-start; gap: 8px; }
  .cpi-tag { margin-left: 0; }
  .footer-links { gap: 16px; flex-wrap: wrap; }
}
</style>
