<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listPosters } from '@/api/posters'
import { listKnowledgeNodes } from '@/api/knowledge'

const auth = useAuthStore()
const router = useRouter()

const hotPosters = ref<any[]>([])
const recentPosters = ref<any[]>([])
const categories = ref<any[]>([])
const featuredPoster = ref<any>(null)
const loading = ref(true)

const typeColors: Record<string, string> = {
  time: 'success',
  place: 'primary',
  organization: 'warning',
  topic: 'danger',
  source: 'info',
}

const nodeTypeLabels: Record<string, string> = {
  time: '时间',
  place: '地点',
  organization: '组织',
  topic: '主题',
  source: '来源',
}

async function fetchData() {
  loading.value = true
  try {
    const [hotRes, recentRes, catRes] = await Promise.all([
      listPosters({ status: 'published', per_page: 3 }),
      listPosters({ per_page: 6 }),
      listKnowledgeNodes(),
    ])
    hotPosters.value = hotRes.data.items
    recentPosters.value = recentRes.data.items
    categories.value = catRes.data.items

    // 取第一个 published 作为今日亮点
    if (hotPosters.value.length > 0) {
      featuredPoster.value = hotPosters.value[0]
    } else if (recentPosters.value.length > 0) {
      featuredPoster.value = recentPosters.value[0]
    }
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function goPosterDetail(id: number) {
  router.push(`/posters/${id}`)
}

onMounted(fetchData)
</script>

<template>
  <div class="home-layout">
    <!-- 左侧侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">导航栏</span>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-item active">首页</div>
        <div class="nav-item">活动分类</div>
        <div class="nav-item">我的主页</div>
      </nav>
    </aside>

    <!-- 右侧主体 -->
    <main class="main-container">
      <!-- 顶栏 -->
      <header class="top-header">
        <div class="header-left">
          <span class="sysu-font">中山大学</span>
          <span class="sys-name">活动管理系统</span>
        </div>
        <div class="header-right">
          <el-button v-if="auth.isLoggedIn" type="primary" class="login-btn" @click="router.push('/dashboard')">进入控制台</el-button>
          <el-button v-else type="primary" class="login-btn" @click="router.push('/auth/login')">登 录</el-button>
        </div>
      </header>

      <!-- 核心内容区 -->
      <div class="content-wrapper">
        <div class="page-intro">
          <div class="breadcrumb">首页 · 活动发现中心</div>
          <div class="intro-header">
            <h1 class="intro-title">逸仙活动云</h1>
            <div class="status-tag">活跃状态 · 在线</div>
          </div>
        </div>

        <!-- 卡片网格 -->
        <div class="bento-grid" v-loading="loading">
          <div class="feature-row">
            <!-- 热门推荐 -->
            <div class="bento-card">
              <h3>热门推荐</h3>
              <div v-if="hotPosters?.length" class="card-list">
                <div
                  v-for="item in hotPosters"
                  :key="item.id"
                  class="card-list-item"
                  @click="goPosterDetail(item.id)"
                >
                  <div class="item-title">{{ item.title }}</div>
                  <div class="item-meta">{{ item.organizer }} · {{ formatTime(item.event_time) }}</div>
                </div>
              </div>
              <div v-else class="card-empty">暂无数据</div>
            </div>

            <!-- 快速筛选（分类标签） -->
            <div class="bento-card">
              <h3>快速筛选</h3>
              <div v-if="categories?.length" class="tag-cloud">
                <el-tag
                  v-for="cat in categories.slice(0, 12)"
                  :key="cat.id"
                  :type="(typeColors[cat.node_type] as any) || 'info'"
                  effect="plain"
                  size="large"
                  style="cursor: pointer; margin: 4px;"
                  @click="router.push(`/knowledge/${cat.id}`)"
                >
                  {{ cat.name }}
                </el-tag>
              </div>
              <div v-else class="card-empty">暂无分类</div>
            </div>

            <!-- 最新发布 -->
            <div class="bento-card">
              <h3>最新发布</h3>
              <div v-if="recentPosters?.length" class="card-list">
                <div
                  v-for="item in recentPosters.slice(0, 4)"
                  :key="item.id"
                  class="card-list-item"
                  @click="goPosterDetail(item.id)"
                >
                  <div class="item-title">{{ item.title }}</div>
                  <div class="item-meta">{{ item.location || '待定' }} · {{ formatTime(item.created_at) }}</div>
                </div>
              </div>
              <div v-else class="card-empty">暂无数据</div>
            </div>
          </div>

          <div class="main-row">
            <!-- 今日亮点 -->
            <div class="bento-card highlight-card">
              <div class="card-header">
                <h3>今日亮点</h3>
                <span class="tag">推荐</span>
              </div>
              <div v-if="featuredPoster" @click="goPosterDetail(featuredPoster.id)" style="cursor: pointer;">
                <div class="featured-title">{{ featuredPoster.title }}</div>
                <div class="featured-summary">{{ featuredPoster.summary || featuredPoster.raw_text?.substring(0, 100) }}</div>
                <div class="featured-meta">
                  <span>📅 {{ formatTime(featuredPoster.event_time) }}</span>
                  <span>📍 {{ featuredPoster.location || '待定' }}</span>
                  <span>🏫 {{ featuredPoster.organizer || '未知' }}</span>
                </div>
              </div>
              <div v-else class="card-empty">暂无推荐活动</div>
            </div>

            <!-- 分类入口 -->
            <div class="bento-card category-card">
              <div class="card-header">
                <h3>分类入口</h3>
                <span class="tag">探索</span>
              </div>
              <div v-if="categories?.length" class="category-grid">
                <div
                  v-for="cat in categories.slice(0, 6)"
                  :key="cat.id"
                  class="category-item"
                  @click="router.push(`/knowledge/${cat.id}`)"
                >
                  <el-tag :type="(typeColors[cat.node_type] as any) || 'info'" size="large" effect="dark">
                    {{ nodeTypeLabels[cat.node_type] || cat.node_type }}
                  </el-tag>
                  <span class="category-name">{{ cat.name }}</span>
                </div>
              </div>
              <div v-else class="card-empty">暂无分类数据</div>
              <div style="margin-top: 16px;">
                <el-button text type="primary" @click="router.push('/knowledge')">查看全部知识节点 →</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.home-layout {
  height: 100vh;
  width: 100vw;
  display: flex;
  overflow: hidden;
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  text-align: left;
}

.home-layout::before {
  content: '';
  position: absolute;
  inset: 0;
  background: url('@/assets/huaishitang.jpg') center / cover no-repeat;
  z-index: 0;
}

.home-layout::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 0;
}

/* ====== 左侧侧边栏 ====== */
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #186c47 0%, #7dc29a 100%);
  color: white;
  display: flex;
  flex-direction: column;
  border-top-right-radius: 24px;
  border-bottom-right-radius: 24px;
  box-shadow: 4px 0 24px rgba(24, 108, 71, 0.15);
  z-index: 10;
  position: relative;
}

.sidebar-header {
  padding: 32px 24px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
}

.sidebar-collapse {
  font-size: 13px;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  transition: color 0.2s;
}

.sidebar-collapse:hover {
  color: white;
}

.sidebar-nav {
  padding: 0 16px;
  flex: 1;
}

.nav-item {
  padding: 14px 20px;
  border-radius: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  font-size: 15px;
  color: rgba(255,255,255,0.85);
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(255,255,255,0.15);
}

.nav-item.active {
  background: rgba(255,255,255,0.25);
  font-weight: 600;
  color: #fff;
}

/* ====== 右侧主体 ====== */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 1;
  color: #fff;
}

/* ====== 顶栏 ====== */
.top-header {
  margin: 20px 32px 0;
  background: white;
  border-radius: 16px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.03);
  flex-shrink: 0;
  color: #333;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.sysu-font {
  font-family: inherit;
  font-size: 26px;
  font-weight: 900;
  color: #10452b;
  letter-spacing: 2px;
}

.sys-name {
  font-size: 15px;
  color: #5d6661;
  font-weight: 500;
  letter-spacing: 1px;
}

.login-btn {
  background: #27a66b;
  border: none;
  padding: 18px 32px;
  font-weight: 600;
  border-radius: 20px;
  letter-spacing: 1px;
  box-shadow: 0 4px 12px rgba(39, 166, 107, 0.2);
  transition: all 0.3s;
}

.login-btn:hover {
  background: #1f8d59;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(39, 166, 107, 0.3);
}

/* ====== 核心内容区 ====== */
.content-wrapper {
  padding: 32px 32px 64px;
  overflow-y: auto;
  flex: 1;
}

.page-intro {
  margin-bottom: 32px;
}

.breadcrumb {
  display: inline-flex;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(8px);
  color: #fff;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 24px;
  border: 1px solid rgba(255,255,255,0.15);
}

.intro-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.intro-title {
  font-size: 28px;
  font-weight: 800;
  color: #fff;
  margin: 0;
  letter-spacing: 1px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

.status-tag {
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(8px);
  color: #fff;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid rgba(255,255,255,0.15);
}

/* ====== 卡片网格 ====== */
.bento-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1100px;
}

.feature-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.main-row {
  display: grid;
  grid-template-columns: 5fr 4fr;
  gap: 24px;
}

.bento-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(255,255,255,0.8);
  transition: transform 0.2s, box-shadow 0.2s;
  color: #333;
}

.bento-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04);
  transform: translateY(-2px);
}

.bento-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #1a3d2c;
  font-weight: 800;
}

.bento-card p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0;
}

.card-header .tag {
  background: #e3f3eb;
  color: #319360;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

/* ====== 卡片列表样式 ====== */
.card-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-list-item {
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.card-list-item:hover {
  background: #f0f9f4;
}

.item-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a3d2c;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  font-size: 12px;
  color: #909399;
}

.card-empty {
  padding: 20px 0;
  text-align: center;
  color: #c0c4cc;
  font-size: 14px;
}

/* ====== 标签云 ====== */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* ====== 今日亮点 ====== */
.featured-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a3d2c;
  margin-bottom: 12px;
}

.featured-summary {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
}

.featured-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #909399;
}

/* ====== 分类网格 ====== */
.category-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.category-item:hover {
  background: #f0f9f4;
}

.category-name {
  font-size: 14px;
  color: #303133;
}
</style>