<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">页面未找到</h2>
      <p class="error-desc">您访问的页面不存在或已被移除</p>
      <div style="margin-top: 24px; display: flex; gap: 12px; justify-content: center;">
        <el-button type="primary" size="large" @click="router.push('/')">返回首页</el-button>
        <el-button size="large" @click="router.back()">返回上一页</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
}

.not-found-content {
  text-align: center;
}

.error-code {
  font-size: 120px;
  font-weight: 800;
  color: #303133;
  margin: 0;
  line-height: 1;
}

.error-title {
  font-size: 28px;
  color: #303133;
  margin: 16px 0 8px;
}

.error-desc {
  font-size: 16px;
  color: #909399;
  margin: 0;
}
</style>
