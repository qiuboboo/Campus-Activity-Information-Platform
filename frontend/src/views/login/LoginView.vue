<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()

const formRef = ref<FormInstance>()
const loading = ref(false)
const showPwd = ref(false)
const rememberMe = ref(localStorage.getItem('remembered_user') !== null)

const form = reactive({
  username: rememberMe.value ? (localStorage.getItem('remembered_user') || '') : '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名/邮箱', trigger: 'blur' },
    { min: 2, message: '用户名至少 2 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 4, message: '密码至少 4 个字符', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.login(form.username, form.password)

    if (rememberMe.value) {
      localStorage.setItem('remembered_user', form.username)
    } else {
      localStorage.removeItem('remembered_user')
    }

    ElMessage.success({
      message: '登录成功，欢迎回来！',
      icon: '<el-icon><SuccessFilled /></el-icon>',
      duration: 2000,
    })
    router.push('/')
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || ''
    if (msg.includes('invalid credentials') || msg.includes('密码') || msg.includes('用户名')) {
      ElMessage.error('用户名或密码错误，请重试')
    } else if (msg.includes('network') || msg.includes('Network')) {
      ElMessage.error('网络连接失败，请检查后端服务是否运行')
    }
    // 其他错误由拦截器处理
  } finally {
    loading.value = false
  }
}

function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="login-wrapper">
    <!-- 背景图片 -->
    <div class="login-bg"></div>
    <div class="login-overlay"></div>

    <!-- 浮动装饰光晕 -->
    <div class="glow-orb glow-orb-1"></div>
    <div class="glow-orb glow-orb-2"></div>

    <!-- 返回首页 -->
    <div class="back-home">
      <el-button text size="small" @click="goHome" style="color: rgba(255,255,255,0.7);">
        <el-icon><ArrowLeft /></el-icon> 返回首页
      </el-button>
    </div>

    <!-- 上方标题 -->
    <div class="top-center-title">
      <h1>逸仙活动云</h1>
      <p class="en-subtitle">Sun Yat-sen University Activity Cloud Platform</p>
    </div>

    <!-- 登录卡片 -->
    <div class="glass-card">
      <div class="card-header">
        <div class="logo-icon">
          <el-icon :size="36" color="#fff"><School /></el-icon>
        </div>
        <h2 class="title">欢迎登录</h2>
        <p class="subtitle">请输入账号信息以继续</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleLogin"
        label-position="top"
        class="login-form"
      >
        <el-form-item label="用户名/邮箱" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名/邮箱"
            size="large"
            :prefix-icon="'User'"
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            :type="showPwd ? 'text' : 'password'"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="'Lock'"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #suffix>
              <el-icon class="pwd-toggle" @click="showPwd = !showPwd">
                <component :is="showPwd ? 'View' : 'Hide'" />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <div class="form-options">
            <el-checkbox v-model="rememberMe" size="small">记住用户名</el-checkbox>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            native-type="submit"
            size="large"
            class="login-btn"
          >
            <template v-if="!loading">
              <el-icon style="margin-right: 6px;"><Key /></el-icon> 登 录
            </template>
            <template v-else>
              <span>登录中...</span>
            </template>
          </el-button>
        </el-form-item>

        <div class="login-tip">
          演示账号：<strong>admin</strong> / <strong>admin123456</strong>
        </div>
      </el-form>
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
  transform: scale(1.05);
  filter: blur(2px);
  transition: transform 6s ease;
}

.login-wrapper:hover .login-bg {
  transform: scale(1);
}

/* ===== 暗色遮罩 ===== */
.login-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(
    135deg,
    rgba(0, 0, 0, 0.45) 0%,
    rgba(0, 0, 0, 0.25) 50%,
    rgba(0, 0, 0, 0.40) 100%
  );
}

/* ===== 浮动光晕 ===== */
.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 1;
  pointer-events: none;
  animation: float-orb 8s ease-in-out infinite;
}

.glow-orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(39, 166, 107, 0.25), transparent);
  top: -100px;
  right: -80px;
}

.glow-orb-2 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.15), transparent);
  bottom: -80px;
  left: -80px;
  animation-delay: -4s;
}

@keyframes float-orb {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

/* ===== 返回首页 ===== */
.back-home {
  position: absolute;
  top: 20px;
  left: 24px;
  z-index: 3;
}

/* ===== 上方标题 ===== */
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
  color: rgba(255, 255, 255, 0.88);
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

/* ===== 半透明玻璃卡片 ===== */
.glass-card {
  position: relative;
  z-index: 2;
  width: min(440px, 90vw);
  padding: 36px 40px 32px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.10),
    0 24px 60px rgba(0, 0, 0, 0.08),
    0 1px 3px rgba(0, 0, 0, 0.05);
  animation: card-enter 0.8s ease-out;
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
  margin-bottom: 28px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 14px;
  background: linear-gradient(135deg, #0b7d5b, #1bbf7a);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(11, 125, 91, 0.30);
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

/* ===== 表单 ===== */
.login-form {
  width: 100%;

  :deep(.el-form-item) {
    margin-bottom: 20px;
  }

  :deep(.el-form-item__label) {
    color: rgba(26, 26, 46, 0.65);
    font-size: 13px;
    font-weight: 500;
    padding-bottom: 4px;
  }

  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(26, 26, 46, 0.10);
    border-radius: 10px;
    box-shadow: none;
    transition: all 0.25s ease;

    &:hover {
      border-color: rgba(11, 125, 91, 0.40);
      background: rgba(255, 255, 255, 0.9);
    }

    &.is-focus {
      border-color: #0b7d5b;
      background: #fff;
      box-shadow: 0 0 0 3px rgba(11, 125, 91, 0.15);
    }
  }

  :deep(.el-input__inner) {
    color: #1a1a2e;
    &::placeholder {
      color: rgba(26, 26, 46, 0.30);
    }
  }

  :deep(.el-input__prefix) {
    color: rgba(26, 26, 46, 0.35);
  }

  /* 密码切换图标 */
  :deep(.pwd-toggle) {
    font-size: 22px;
    color: rgba(26, 26, 46, 0.35);
    cursor: pointer;
    border-radius: 6px;
    padding: 4px;
    transition: all 0.2s ease;

    &:hover {
      color: #0b7d5b;
      background: rgba(11, 125, 91, 0.08);
    }

    &:active {
      background: rgba(11, 125, 91, 0.15);
    }
  }

  /* 校验错误样式 */
  :deep(.el-form-item.is-error .el-input__wrapper) {
    border-color: #f56c6c;
    box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.12);
  }
}

/* ===== 表单选项 ===== */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.form-options :deep(.el-checkbox__label) {
  font-size: 13px;
  color: rgba(26, 26, 46, 0.55);
}

/* ===== 登录按钮 ===== */
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

/* ===== 提示信息 ===== */
.login-tip {
  text-align: center;
  font-size: 12px;
  color: rgba(26, 26, 46, 0.35);
  margin-top: -8px;
}

.login-tip strong {
  color: rgba(26, 26, 46, 0.50);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .top-center-title {
    top: 24px;
  }

  .top-center-title h1 {
    font-size: 36px;
    letter-spacing: 2px;
  }

  .en-subtitle {
    font-size: 14px;
    margin-top: 4px;
  }

  .glass-card {
    padding: 28px 24px 24px;
    width: 92vw;
  }

  .logo-icon {
    width: 52px;
    height: 52px;
  }

  .logo-icon :deep(.el-icon) {
    font-size: 28px !important;
  }

  .title {
    font-size: 19px;
  }
}

@media (max-width: 480px) {
  .back-home {
    top: 12px;
    left: 12px;
  }

  .top-center-title h1 {
    font-size: 28px;
  }

  .glass-card {
    padding: 24px 18px 20px;
  }

  .login-btn {
    height: 44px;
    font-size: 15px;
  }
}
</style>
