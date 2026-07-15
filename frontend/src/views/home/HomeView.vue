<script setup lang="ts">
import { TrendCharts, Collection, Clock, Calendar, Location, User, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useHomePage } from '@/composables/useHomePage'
import NavHeader from '@/components/NavHeader.vue'
import NavSidebar from '@/components/NavSidebar.vue'
import HomeCalendarCard from '@/components/HomeCalendarCard.vue'
import FooterBar from '@/components/FooterBar.vue'
import ActivityCover from '@/components/ActivityCover.vue'

const {
  auth, router,
  hotActivities, recentActivities, activityTypeList, loading, error, scheduleError, searchKeyword,
  currentHotIndex, isHotCarouselPaused, startHotCarousel, toggleHotCarousel,
  activeNav, selectNav,
  currentYear, currentMonth, selectedDate, weekDays,
  calendarDays, prevMonth, nextMonth, selectDate, selectedScheduleItems,
  selectedCategoryId, categoryActivities, fetchCategoryActivities, selectCategory,
  fetchData, fetchSchedule, formatTime, goActivityDetail, handleSearch, handleLogout, currentYearLabel
} = useHomePage()
</script>

<template>
  <div class="home-page">
    <NavHeader
      :search-keyword="searchKeyword"
      :is-logged-in="auth.isLoggedIn"
      :is-publisher="auth.isPublisher"
      :is-admin="auth.isAdmin"
      :username="auth.user?.username ?? null"
      @update:search-keyword="searchKeyword = $event"
      @search="handleSearch"
      @login="router.push('/auth/login')"
      @register="router.push('/auth/register')"
      @profile="router.push('/profile')"
      @my-activities="router.push('/my/activities')"
      @admin="router.push('/admin')"
      @logout="handleLogout"
      @go-home="router.push('/')"
    />

    <div class="home-body">
      <NavSidebar
        :active-nav="activeNav"
        :activity-type-list="activityTypeList"
        :selected-category-id="selectedCategoryId"
        @select-nav="selectNav"
        @select-category="selectCategory"
      />

      <main class="home-main">
        <div id="section-hot" class="hot-section" v-if="!loading && !error">
          <div class="section-header">
            <h2 class="section-title">
              <el-icon class="section-title-icon"><TrendCharts /></el-icon>
              热门活动
            </h2>
            <el-button text class="section-more" @click="router.push('/activities')">
              查看全部 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
          <article v-if="hotActivities.length > 0" class="hot-carousel" aria-label="热门活动轮播">
            <div class="hc-cover">
              <ActivityCover
                :src="hotActivities[currentHotIndex].cover_image_url"
                :category="hotActivities[currentHotIndex].activity_type"
                :alt="hotActivities[currentHotIndex].title"
              />
            </div>
            <div class="hc-card">
              <div class="hc-badge">
                <el-tag
                  :type="hotActivities[currentHotIndex].activity_type ? 'success' : 'info'"
                  size="small" effect="plain" round
                >
                  {{ hotActivities[currentHotIndex].activity_type || '活动' }}
                </el-tag>
              </div>
              <h3 class="hc-title">{{ hotActivities[currentHotIndex].title }}</h3>
              <p class="hc-summary">
                {{ hotActivities[currentHotIndex].summary || hotActivities[currentHotIndex].raw_text?.substring(0, 80) || '暂无简介' }}
              </p>
              <div class="hc-meta">
                <span><el-icon size="14"><User /></el-icon> {{ hotActivities[currentHotIndex].organizer || '未知' }}</span>
                <span><el-icon size="14"><Clock /></el-icon> {{ formatTime(hotActivities[currentHotIndex].event_time) }}</span>
                <span><el-icon size="14"><Location /></el-icon> {{ hotActivities[currentHotIndex].location || '待定' }}</span>
              </div>
            </div>
            <div class="hc-dots" v-if="hotActivities.length > 1">
              <button
                v-for="(_, i) in hotActivities" :key="i"
                class="hc-dot" :class="{ active: i === currentHotIndex }" :aria-label="`显示第 ${i + 1} 条热门活动`" :aria-current="i === currentHotIndex ? 'true' : undefined"
                @click.stop="currentHotIndex = i; startHotCarousel()"
              ></button>
            </div>
            <div class="hc-actions"><el-button type="primary" @click="goActivityDetail(hotActivities[currentHotIndex].id)">查看活动</el-button><el-button v-if="hotActivities.length > 1" text @click="toggleHotCarousel">{{ isHotCarouselPaused ? '恢复轮播' : '暂停轮播' }}</el-button></div>
          </article>
          <div v-else class="hot-empty">
            <el-empty :image-size="80" description="暂无活动" />
          </div>
        </div>

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
          <section v-else-if="error" class="home-error"><el-result icon="error" title="活动加载失败" :sub-title="error"><template #extra><el-button type="primary" @click="fetchData">重试</el-button></template></el-result></section>
          <template v-else>
            <section class="content-section" id="section-categories">
              <div class="section-header">
                <h2 class="section-title">
                  <el-icon class="section-title-icon"><Collection /></el-icon>
                  活动分类
                </h2>
              </div>
              <div class="category-tabs">
                <el-radio-group v-model="selectedCategoryId" @change="fetchCategoryActivities">
                  <el-radio-button value="recent">最近</el-radio-button>
                  <el-radio-button v-for="cat in activityTypeList" :key="cat" :value="cat">
                    {{ cat }}
                  </el-radio-button>
                </el-radio-group>
              </div>
            </section>
            <div class="cat-scroll-body">
              <div class="cat-activity-list" v-if="categoryActivities.length > 0">
                <button v-for="p in categoryActivities" :key="p.id" type="button" class="cat-activity-item" @click="goActivityDetail(p.id)">
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
                </button>
              </div>
              <div v-else class="cat-activity-empty">
                <el-empty :image-size="80" description="该类别暂无活动" />
              </div>
            </div>
            <section class="content-section" v-if="hotActivities.length === 0 && recentActivities.length === 0">
              <div class="empty-state">
                <el-empty description="暂无活动数据，请稍后再来">
                  <el-button type="primary" @click="fetchData">刷新</el-button>
                </el-empty>
              </div>
            </section>
          </template>
        </div>
      </main>

      <aside class="side-right">
        <HomeCalendarCard
          :current-year="currentYear"
          :current-month="currentMonth"
          :week-days="weekDays"
          :calendar-days="calendarDays"
          :selected-date="selectedDate"
          :schedule-items="selectedScheduleItems"
          :schedule-error="scheduleError"
          @prev-month="prevMonth"
          @next-month="nextMonth"
          @select-date="selectDate"
          @retry-schedule="fetchSchedule"
        />
      </aside>
    </div>

    <FooterBar :current-year-label="currentYearLabel" />

    <el-backtop :visibility-height="400" :right="32" :bottom="40" />
  </div>
</template>

<style scoped>
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

/* ---- 三栏主体布局 ---- */
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

/* ---- 中间主内容 ---- */
.home-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.hot-section { flex-shrink: 0; }

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

.cat-scroll-body::-webkit-scrollbar { width: 4px; }
.cat-scroll-body::-webkit-scrollbar-thumb { background: #d0d0d0; border-radius: 2px; }

.content-section { margin-bottom: 20px; }

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

.section-title-icon { font-size: 20px; color: #27a66b; }

.section-more {
  color: #0b7d5b !important;
  font-size: 13px;
  transition: color 0.2s;
}

.section-more:hover {
  color: #0ea36f !important;
  background: rgba(11, 125, 91, 0.06) !important;
}

/* ---- 卡片入场动画 ---- */
@keyframes card-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.hot-carousel, .cat-activity-item { animation: card-in 0.5s ease-out both; }
.hot-carousel { animation-delay: 0s; }
.cat-activity-item:nth-child(1) { animation-delay: 0.05s; }
.cat-activity-item:nth-child(2) { animation-delay: 0.1s; }
.cat-activity-item:nth-child(3) { animation-delay: 0.15s; }
.cat-activity-item:nth-child(4) { animation-delay: 0.2s; }
.cat-activity-item:nth-child(5) { animation-delay: 0.25s; }
.cat-activity-item:nth-child(6) { animation-delay: 0.3s; }

/* ---- 骨架屏 ---- */
.skeleton-title {
  height: 24px; width: 140px;
  background: linear-gradient(90deg, #e8e8e8 25%, #f5f5f5 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: 6px; margin-bottom: 16px;
}

.skeleton-scroll { display: flex; gap: 16px; overflow: hidden; }

.skeleton-card-scroll {
  width: 240px; height: 160px;
  background: linear-gradient(90deg, #e8e8e8 25%, #f5f5f5 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: 16px; flex-shrink: 0;
}

.skeleton-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }

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

/* ---- 热门轮播 ---- */
.hot-carousel {
  background: #fff;
  border-radius: 14px;
  padding: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04);
  border-left: 4px solid #27a66b;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  position: relative;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  overflow: hidden;
}

.hot-carousel:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(13, 94, 60, 0.08);
}

.hot-empty {
  display: flex; align-items: center; justify-content: center;
  min-height: 180px; background: #fff;
  border: 1px dashed #d8dee9; border-radius: 14px;
}

.hc-cover {
  min-height: 210px;
  display: grid;
  font-size: 24px;
}
.hc-card { padding: 28px 32px 20px; min-width: 0; }

.hc-badge { margin-bottom: 12px; }

.hc-title {
  font-size: 20px; font-weight: 800;
  color: #0d5e3c; margin: 0 0 10px;
}

.hc-summary {
  font-size: 14px; color: #606266; line-height: 1.6;
  margin: 0 0 16px;
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}

.hc-meta { display: flex; gap: 20px; font-size: 13px; color: #909399; flex-wrap: wrap; }
.hc-meta span { display: flex; align-items: center; gap: 4px; }

.hc-dots { display: flex; justify-content: center; gap: 8px; margin-top: 16px; }

.hc-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #d0d0d0; cursor: pointer; transition: all 0.25s; border: 0; padding: 0;
}

.hc-dot.active { background: #27a66b; width: 24px; border-radius: 4px; }
.hc-dot:hover { background: #27a66b; }
.hc-actions { display: flex; align-items: center; gap: 8px; margin-top: 14px; }

/* ---- 分类标签 ---- */
.category-tabs {
  margin-bottom: 8px;
  overflow-x: auto;
  white-space: nowrap;
  padding-bottom: 4px;
}

.category-tabs :deep(.el-radio-group) { display: inline-flex; gap: 0; flex-wrap: nowrap; }
.category-tabs :deep(.el-radio-button__inner) { font-size: 13px; padding: 8px 16px; border-color: #e8e8e8; }

.cat-activity-list { display: flex; flex-direction: column; gap: 8px; }

.cat-activity-item {
  background: #fff; border-radius: 12px;
  padding: 16px 20px;
  display: flex; align-items: center; justify-content: space-between;
  cursor: pointer; transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  border: 0;
  width: 100%;
  text-align: left;
}

.cat-activity-item:hover { background: #f5fcf8; transform: translateX(4px); }

.cpi-left { flex: 1; min-width: 0; }

.cpi-title {
  font-size: 14px; font-weight: 600; color: #0d5e3c;
  margin-bottom: 4px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.cpi-meta { font-size: 12px; color: #909399; display: flex; gap: 16px; }
.cpi-meta span { display: flex; align-items: center; gap: 4px; }
.cpi-tag { flex-shrink: 0; margin-left: 12px; }
.cat-activity-empty { padding: 24px 0; }

.empty-state { background: #fff; border-radius: 14px; padding: 40px 0; }
.home-error { background: #fff; border-radius: 14px; }

/* ---- 右侧辅助栏容器 ---- */
.side-right {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

/* ---- 响应式 ---- */
@media (max-width: 1024px) {
  .side-right { display: none; }
  .home-body { gap: 20px; }
}

@media (max-width: 768px) {
  .home-page { height: auto; min-height: 100svh; overflow: visible; }
  .home-body,.home-main,.category-scroll { overflow: visible; }
  .cat-scroll-body { overflow: visible; }
  .side-left { display: none; }
  .home-body { padding: 16px 16px 0; flex-direction: column; }
  .section-title { font-size: 17px; }
  .hc-summary { font-size: 13px; }
  .hot-carousel { grid-template-columns: 1fr; }
  .hc-cover { min-height: 140px; }
}

@media (max-width: 480px) {
  .home-body { padding: 12px; }
  .category-tabs :deep(.el-radio-button__inner) { padding: 6px 12px; font-size: 12px; }
  .cat-activity-item { padding: 12px 16px; flex-direction: column; align-items: flex-start; gap: 8px; }
  .cpi-tag { margin-left: 0; }
}
</style>
