<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

interface MenuItem {
  path: string
  label: string
  icon: string
  adminOnly?: boolean
}

const menuItems = computed<MenuItem[]>(() => [
  { path: '/dashboard', label: '数据看板', icon: 'DataAnalysis' },
  { path: '/posters', label: '活动海报', icon: 'Document' },
  { path: '/knowledge', label: '知识图谱', icon: 'Connection' },
  { path: '/search', label: '搜索', icon: 'Search' },
  { path: '/posters/review', label: '审核队列', icon: 'Finished', adminOnly: true },
  { path: '/datasources', label: '数据源管理', icon: 'Setting', adminOnly: true },
  { path: '/audit-logs', label: '审计日志', icon: 'List', adminOnly: true },
])

const visibleMenuItems = computed(() =>
  menuItems.value.filter((item) => !item.adminOnly || auth.isAdmin),
)

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

function handleLogout() {
  auth.logout()
  router.push('/auth/login')
}

function goHome() {
  router.push('/dashboard')
}
</script>

<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside width="220px" style="background: #304156; overflow-y: auto;">
      <div
        style="height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: bold; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.1);"
        @click="goHome"
      >
        <el-icon size="22" style="margin-right: 8px;"><School /></el-icon>
        <span>校园活动平台</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item
          v-for="item in visibleMenuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主区域 -->
    <el-container>
      <el-header
        style="
          display: flex;
          justify-content: flex-end;
          align-items: center;
          height: 60px;
          background: #fff;
          border-bottom: 1px solid #e6e6e6;
          padding: 0 24px;
        "
      >
        <div style="display: flex; align-items: center; gap: 12px;">
          <el-tag :type="auth.isAdmin ? 'danger' : 'info'" size="small" effect="dark">
            {{ auth.user?.role }}
          </el-tag>
          <span style="color: #333; font-size: 14px;">{{ auth.user?.username }}</span>
          <el-button size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main style="background: #f0f2f5; padding: 20px; overflow-y: auto;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
