<template>
  <nav class="home-nav">
    <div class="nav-inner">
      <button class="nav-brand" type="button" aria-label="返回首页" @click="$emit('goHome')">
        <span class="nav-brand-title">逸仙活动云</span>
      </button>

      <SearchBar
        :search-keyword="searchKeyword"
        @update:search-keyword="$emit('update:searchKeyword', $event)"
        @search="$emit('search')"
      />

      <div class="nav-actions">
        <template v-if="isLoggedIn">
          <el-button text class="nav-profile" @click="$emit('profile')">{{ username }}</el-button>
          <el-button v-if="isPublisher" text class="nav-profile" @click="$emit('myActivities')">我的发布</el-button>
          <el-button v-if="isAdmin" text class="nav-profile" @click="$emit('admin')">管理</el-button>
          <el-button type="primary" class="nav-cta" @click="$emit('logout')">退出登录</el-button>
        </template>
        <template v-else>
          <el-button text class="nav-register" @click="$emit('register')">注册</el-button>
          <el-button type="primary" class="nav-cta" @click="$emit('login')">登录</el-button>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import SearchBar from './SearchBar.vue'

defineProps<{
  searchKeyword: string
  isLoggedIn: boolean
  isPublisher?: boolean
  isAdmin?: boolean
  username: string | null
}>()

defineEmits<{
  (e: 'goHome'): void
  (e: 'update:searchKeyword', v: string): void
  (e: 'search'): void
  (e: 'login'): void
  (e: 'register'): void
  (e: 'profile'): void
  (e: 'myActivities'): void
  (e: 'admin'): void
  (e: 'logout'): void
}>()
</script>

<style scoped>
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
  padding: 0;
  border: 0;
  background: transparent;
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
  margin-right: -8px;
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

.nav-cta:active,
.nav-cta:focus {
  background: #27a66b !important;
}

.nav-user {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 18px;
  font-weight: 600;
}
.nav-profile,.nav-register { color: rgb(255 255 255 / 90%) !important; }

@media (max-width: 768px) {
  .nav-brand-title { font-size: 22px; }
  .nav-inner { padding: 0 16px; }
}

@media (max-width: 480px) {
  .nav-inner { padding: 0 12px; }
}
</style>
