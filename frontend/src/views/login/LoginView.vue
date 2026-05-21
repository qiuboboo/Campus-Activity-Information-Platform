<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()
const form = ref({
  username: '',
  password: '',
})
const loading = ref(false)
const showPwd = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <!-- 动态渐变背景 -->
    <div class="login-bg"></div>
    <div class="login-overlay"></div>

    <!-- 上方居中大标题 -->
    <div class="top-center-title">
      <h1>逸仙活动云</h1>
      <p class="en-subtitle">Sun Yat-sen University Activity Cloud Platform</p>
    </div>

    <!-- 登录卡片 -->
    <div class="glass-card">
      <div class="card-header">
        <h2 class="title">用户登录</h2>
      </div>

      <div class="form-center">
      <el-form :model="form" @submit.prevent="handleLogin" label-position="top" class="login-form">
        <el-form-item label="用户名/邮箱">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名/邮箱"
            size="large"
            :prefix-icon="'User'"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            :type="showPwd ? 'text' : 'password'"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="'Lock'"
          >
            <template #suffix>
              <el-icon
                class="pwd-toggle"
                @click="showPwd = !showPwd"
              >
                <component :is="showPwd ? 'View' : 'Hide'" />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            native-type="submit"
            size="large"
            class="login-btn"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ===== 容器 ===== */
.login-wrapper {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
}

/* ===== 背景图片 ===== */
.login-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: url('@/assets/huaishitang.jpg') center / cover no-repeat;
}

/* ===== 暗色遮罩 ===== */
.login-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: rgba(0, 0, 0, 0.35);
}

/* ===== 上方居中大标题 ===== */
.top-center-title {
  position: absolute;
  top: 48px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
  text-align: center;
}

.top-center-title h1 {
  font-size: 64px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 4px;
  margin: 0;
  text-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.6), 
    0 2px 4px rgba(0, 0, 0, 0.4);
}
.en-subtitle {
  font-size: 24px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.75);
  letter-spacing: 1px;
  margin: 6px 0 0 2px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}
/* ===== 半透明立体卡片 ===== */
.glass-card {
  position: relative;
  z-index: 2;
  width: min(520px, 88vw);
  aspect-ratio: 16 / 9;
  padding: 32px 48px 28px;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.10),
    0 24px 60px rgba(0, 0, 0, 0.08),
    0 1px 3px rgba(0, 0, 0, 0.05);
  animation: card-enter 0.8s ease-out;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ===== 卡片头部 ===== */
.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #0b7d5b, #1bbf7a);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(11, 125, 91, 0.35);
}

.title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 6px;
  letter-spacing: 1px;
}

.subtitle {
  font-size: 13px;
  color: rgba(26, 26, 46, 0.45);
  letter-spacing: 0.5px;
}

/* ===== 表单居中容器 ===== */
.form-center {
  display: flex;
  justify-content: center;
}

/* ===== 表单 ===== */
.login-form {
  width: 100%;
  max-width: 340px;
  :deep(.el-form-item__label) {
    color: rgba(26, 26, 46, 0.65);
    font-size: 13px;
    font-weight: 500;
  }

  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(26, 26, 46, 0.1);
    border-radius: 10px;
    box-shadow: none;
    transition: all 0.3s ease;

    &:hover {
      border-color: rgba(11, 125, 91, 0.45);
      background: rgba(255, 255, 255, 0.9);
    }

    &.is-focus {
      border-color: #0b7d5b;
      background: #fff;
      box-shadow: 0 0 0 3px rgba(11, 125, 91, 0.18);
    }
  }

  :deep(.el-input__inner) {
    color: #1a1a2e;
    &::placeholder {
      color: rgba(26, 26, 46, 0.3);
    }
  }

  :deep(.el-input__prefix) {
    color: rgba(26, 26, 46, 0.35);
  }

  /* 密码切换图标按钮 */
  :deep(.pwd-toggle) {
    font-size: 24px;
    color: rgba(26, 26, 46, 0.4);
    cursor: pointer;
    border-radius: 6px;
    padding: 4px;
    transition: all 0.2s ease;

    &:hover {
      color: #0b7d5b;
      background: rgba(11, 125, 91, 0.10);
    }

    &:active {
      background: rgba(11, 125, 91, 0.18);
    }
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0b7d5b, #1bbf7a);
  border: none;
  transition: all 0.3s ease;

  &:hover {
    background: linear-gradient(135deg, #0ea36f, #22c98a);
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(11, 125, 91, 0.35);
  }

  &:active {
    transform: translateY(0);
  }
}
</style>
