<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <main v-if="!auth.ready" class="app-loading" aria-live="polite">
    <el-icon class="is-loading" :size="28"><Loading /></el-icon>
    <span>正在验证登录状态…</span>
  </main>
  <router-view v-else />
</template>

<style scoped>
.app-loading { min-height: 100vh; display: grid; place-content: center; gap: 14px; color: var(--brand-dark); font-weight: 600; background: var(--surface-muted); }
</style>
