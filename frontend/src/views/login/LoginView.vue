<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ username: 'admin', password: 'admin123456' })
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-bg"></div>
    <el-card class="login-card" shadow="always">
      <div style="text-align: center; margin-bottom: 28px;">
        <el-icon size="48" color="#409eff"><School /></el-icon>
        <h2 style="margin-top: 12px; color: #303133;">校园活动信息平台</h2>
        <p style="color: #909399; margin-top: 4px; font-size: 14px;">Campus Activity Information Platform</p>
      </div>
      <el-form :model="form" @submit.prevent="handleLogin" label-position="top">
        <el-form-item label="用户名">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="'User'"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            size="large"
            :prefix-icon="'Lock'"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            native-type="submit"
            size="large"
            style="width: 100%"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center; margin-top: 12px; color: #c0c4cc; font-size: 12px;">
        默认管理员账号: admin / admin123456
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.login-wrapper {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
}
.login-bg {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: 0;
}
.login-card {
  width: 420px;
  z-index: 1;
  border-radius: 12px;
  padding: 16px;
}
</style>
