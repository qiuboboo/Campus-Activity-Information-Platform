<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = withDefaults(defineProps<{ title?: string; showSearch?: boolean }>(), {
  title: '',
  showSearch: true,
})
const auth = useAuthStore()
const router = useRouter()
const searchKeyword = ref(String(router.currentRoute.value.query.q || ''))

function search(value: string) {
  const q = value.trim()
  router.push({ path: '/search', query: q ? { q } : {} })
}

function logout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="app-header__inner">
        <button class="brand" type="button" aria-label="返回首页" @click="router.push('/')">逸仙活动云</button>
        <el-input
          v-if="showSearch"
          v-model="searchKeyword"
          class="header-search"
          placeholder="搜索活动、地点或主办方"
          clearable
          @keyup.enter="search(searchKeyword)"
          @clear="search('')"
        />
        <nav class="header-nav" aria-label="主导航">
          <el-button text @click="router.push('/activities')">活动</el-button>
          <el-button v-if="auth.isLoggedIn" text @click="router.push('/calendar')">日历</el-button>
          <template v-if="auth.isLoggedIn">
            <el-button text @click="router.push('/profile')">{{ auth.user?.display_name || auth.user?.username }}</el-button>
            <el-button v-if="auth.isPublisher" text @click="router.push('/my/activities')">我的发布</el-button>
            <el-button v-if="auth.isAdmin" text @click="router.push('/admin')">管理</el-button>
            <el-button class="header-cta" type="primary" @click="logout">退出</el-button>
          </template>
          <template v-else>
            <el-button text @click="router.push('/auth/login')">登录</el-button>
            <el-button class="header-cta" type="primary" @click="router.push('/auth/register')">注册</el-button>
          </template>
        </nav>
      </div>
    </header>
    <main class="app-main" :class="{ 'app-main--titled': title }">
      <div v-if="title" class="page-heading"><h1>{{ title }}</h1><slot name="heading" /></div>
      <slot />
    </main>
  </div>
</template>

<style scoped>
.app-shell { min-height: 100vh; background: var(--surface-muted); }
.app-header { position: sticky; top: 0; z-index: 30; background: var(--brand); border-bottom: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 2px 10px rgb(13 94 60 / 15%); }
.app-header__inner { height: 60px; max-width: 1400px; margin: 0 auto; padding: 0 32px; display: flex; gap: 24px; align-items: center; }
.brand { border: 0; background: transparent; color: #fff; cursor: pointer; font-size: 23px; font-weight: 800; letter-spacing: 1px; white-space: nowrap; }
.header-search { max-width: 480px; flex: 1; }
.header-search :deep(.el-input__wrapper) { border-radius: 999px; }
.header-nav { margin-left: auto; display: flex; gap: 8px; align-items: center; white-space: nowrap; }
.header-nav :deep(.el-button--text) {
  min-height: 34px;
  padding: 8px 13px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 18px;
  color: rgb(255 255 255 / 92%) !important;
  font-weight: 600;
}
.header-nav :deep(.el-button--text:hover),
.header-nav :deep(.el-button--text:focus) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.34);
  color: #fff !important;
}
.header-cta {
  border: 0 !important;
  border-radius: 20px;
  background: var(--brand-accent) !important;
  color: #fff !important;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(39, 166, 107, 0.25);
}
.header-cta:hover,
.header-cta:focus {
  background: #1f8d59 !important;
  color: #fff !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(39, 166, 107, 0.35);
}
.app-main { max-width: 1280px; margin: 0 auto; padding: 32px 24px 48px; }
.page-heading { display: flex; gap: 16px; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-heading h1 { margin: 0; color: var(--brand-dark); font-size: 26px; }
@media (max-width: 900px) { .header-search { display: none; } .header-nav { overflow-x: auto; } }
@media (max-width: 600px) { .app-header__inner { padding: 0 12px; gap: 8px; } .brand { font-size: 19px; } .header-nav { gap: 4px; } .header-nav :deep(.el-button--text) { padding-left: 8px; padding-right: 8px; } .app-main { padding: 20px 14px 32px; } }
</style>
