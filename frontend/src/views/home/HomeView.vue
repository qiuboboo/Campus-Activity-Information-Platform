<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
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
          <el-button v-else type="primary" class="login-btn" @click="router.push('/login')">登 录</el-button>
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

        <!-- 卡片网格（预留 API 数据展示位） -->
        <div class="bento-grid">
          <div class="feature-row">
            <div class="bento-card">
              <h3>热门推荐</h3>
              <!-- API: 热门活动列表 -->
            </div>
            <div class="bento-card">
              <h3>快速筛选</h3>
              <!-- API: 分类筛选入口 -->
            </div>
            <div class="bento-card">
              <h3>最新发布</h3>
              <!-- API: 最新活动列表 -->
            </div>
          </div>

          <div class="main-row">
            <div class="bento-card highlight-card">
              <div class="card-header">
                <h3>今日亮点</h3>
                <span class="tag">推荐</span>
              </div>
              <!-- API: 精选活动展示 -->
            </div>

            <div class="bento-card category-card">
              <div class="card-header">
                <h3>分类入口</h3>
                <span class="tag">探索</span>
              </div>
              <!-- API: 活动分类列表 -->
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
</style>