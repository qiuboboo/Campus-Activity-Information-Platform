<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { register as registerApi } from '@/api/auth'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()

const formRef = ref<FormInstance>()
const loading = ref(false)
const showPwd = ref(false)
const showConfirmPwd = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'viewer',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, message: '用户名至少 2 个字符', trigger: 'blur' },
    { max: 50, message: '用户名不能超过 50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleRegister() {
  if (!form.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!form.password) {
    ElMessage.warning('请输入密码')
    return
  }
  if (form.password.length < 6) {
    ElMessage.warning('密码至少 6 个字符')
    return
  }
  if (form.password !== form.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    await registerApi({
      username: form.username.trim(),
      password: form.password,
      role: form.role,
    })
    ElMessage.success('注册成功，请登录')
    router.push('/auth/login')
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || ''
    if (msg.includes('already exists')) {
      ElMessage.error('用户名已存在')
    } else if (msg.includes('network') || msg.includes('Network') || msg.includes('connect')) {
      ElMessage.error('网络连接失败，请检查后端服务是否运行')
    } else if (msg) {
      ElMessage.error(msg)
    }
  } finally {
    loading.value = false
  }
}

function goHome() {
  router.push('/')
}

const roleOptions = [
  { value: 'viewer', label: '浏览者（仅查看）' },
  { value: 'publisher', label: '发布者（可创建活动）' },
]
</script>

<template>
  <div class="register-wrapper">
    <div class="register-bg"></div>
    <div class="register-overlay"></div>

    <div class="back-home">
      <el-button @click="goHome" class="back-home-btn">返回首页</el-button>
    </div>

    <div class="top-center-title">
      <h1>逸仙活动云</h1>
      <p class="en-subtitle">Sun Yat-sen University Activity Cloud Platform</p>
    </div>

    <div class="half-transparent-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleRegister"
        label-position="top"
        class="register-form"
      >
        <h2 style="text-align: center; margin-bottom: 16px; color: #303133; font-size: 24px;">用户注册</h2>

        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="2-50 个字符"
            size="large"
            :prefix-icon="'User'"
            clearable
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            :type="showPwd ? 'text' : 'password'"
            placeholder="至少 6 个字符"
            size="large"
            :prefix-icon="'Lock'"
            @keyup.enter="handleRegister"
          >
            <template #suffix>
              <el-icon class="pwd-toggle" @click="showPwd = !showPwd">
                <component :is="showPwd ? 'View' : 'Hide'" />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            :type="showConfirmPwd ? 'text' : 'password'"
            placeholder="再次输入密码"
            size="large"
            :prefix-icon="'Lock'"
            @keyup.enter="handleRegister"
          >
            <template #suffix>
              <el-icon class="pwd-toggle" @click="showConfirmPwd = !showConfirmPwd">
                <component :is="showConfirmPwd ? 'View' : 'Hide'" />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option v-for="opt in roleOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" size="large" class="register-btn" @click="handleRegister">
            {{ loading ? '注册中...' : '注 册' }}
          </el-button>
        </el-form-item>

        <div style="text-align: center; margin-top: 4px;">
          <span style="font-size: 13px; color: rgba(26,26,46,0.45);">
            已有账号？
            <router-link to="/auth/login" style="color: #0b7d5b; font-weight: 500;">去登录</router-link>
          </span>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.register-wrapper { height: 100vh; width: 100vw; display: flex; justify-content: center; align-items: center; position: relative; overflow: hidden; }
.register-bg { position: absolute; inset: 0; z-index: 0; background: url('@/assets/huaishitang.jpg') center / cover no-repeat; }
.register-overlay { position: absolute; inset: 0; z-index: 1; background: linear-gradient(135deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0.25) 50%, rgba(0,0,0,0.40) 100%); }
.back-home { position: absolute; top: 20px; left: 24px; z-index: 3; }
.back-home-btn { color: rgba(255,255,255,0.85) !important; font-size: 16px; background: transparent !important; }
.back-home-btn:hover { background: transparent !important; }
.top-center-title { position: absolute; top: 48px; left: 50%; transform: translateX(-50%); z-index: 2; text-align: center; }
.top-center-title h1 { font-size: 64px; font-weight: 800; color: rgba(255,255,255,0.88); letter-spacing: 4px; margin: 0; text-shadow: 0 4px 12px rgba(0,0,0,0.6), 0 2px 4px rgba(0,0,0,0.4); }
.en-subtitle { font-size: 24px; font-weight: 400; color: rgba(255,255,255,0.75); letter-spacing: 1px; margin: 6px 0 0 2px; text-shadow: 0 2px 8px rgba(0,0,0,0.5); }
.half-transparent-card { position: relative; z-index: 2; width: min(460px, 92vw); aspect-ratio: 16/9; padding: 22px 32px 18px; background: rgba(255,255,255,0.75); border-radius: 20px; border: 1px solid rgba(255,255,255,0.5); box-shadow: 0 8px 32px rgba(0,0,0,0.10), 0 24px 60px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.05); animation: card-enter 0.8s ease-out; display: flex; flex-direction: column; justify-content: center; }
@keyframes card-enter { from { opacity: 0; transform: translateY(30px) scale(0.96); } to { opacity: 1; transform: translateY(0) scale(1); } }
.register-form { width: 100%; }
.register-form :deep(.el-form-item) { margin-bottom: 12px; }
.register-form :deep(.el-form-item__label) { color: rgba(26,26,46,0.65); font-size: 13px; font-weight: 500; padding-bottom: 4px; }
.register-form :deep(.el-input__wrapper) { background: rgba(255,255,255,0.7); border: 1px solid rgba(26,26,46,0.10); border-radius: 10px; box-shadow: none; transition: all 0.25s ease; }
.register-form :deep(.el-input__wrapper:hover) { border-color: rgba(11,125,91,0.40); background: rgba(255,255,255,0.9); }
.register-form :deep(.el-input__wrapper.is-focus) { border-color: #0b7d5b; background: #fff; box-shadow: 0 0 0 3px rgba(11,125,91,0.15); }
.register-form :deep(.el-input__inner) { color: #1a1a2e; }
.register-form :deep(.el-input__inner::placeholder) { color: rgba(26,26,46,0.30); }
.register-form :deep(.el-input__prefix) { color: rgba(26,26,46,0.35); }
.register-form :deep(.pwd-toggle) { font-size: 22px; color: rgba(26,26,46,0.35); cursor: pointer; border-radius: 6px; padding: 4px; transition: all 0.2s ease; }
.register-form :deep(.pwd-toggle:hover) { color: #0b7d5b; background: rgba(11,125,91,0.08); }
.register-btn { width: 100%; height: 48px; font-size: 16px; font-weight: 600; letter-spacing: 2px; border-radius: 10px; background: linear-gradient(135deg,#0b7d5b,#1bbf7a); border: none; transition: all 0.3s ease; }
.register-btn:hover { background: linear-gradient(135deg,#0ea36f,#22c98a); transform: translateY(-1px); box-shadow: 0 8px 20px rgba(11,125,91,0.35); }
@media (max-width: 768px) { .top-center-title { top: 24px; } .top-center-title h1 { font-size: 36px; letter-spacing: 2px; } .en-subtitle { font-size: 14px; margin-top: 4px; } .half-transparent-card { padding: 24px 20px 20px; width: 92vw; } }
@media (max-width: 480px) { .back-home { top: 12px; left: 12px; } .top-center-title h1 { font-size: 28px; } .half-transparent-card { padding: 24px 18px 20px; } .register-btn { height: 44px; font-size: 15px; } }
</style>
