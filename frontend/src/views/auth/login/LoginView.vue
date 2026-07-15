<script setup lang="ts">
import { computed, ref, reactive } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { ElMessage } from "element-plus"
import type { FormInstance, FormRules } from "element-plus"
import AuthLayout from "@/components/AuthLayout.vue"
import { passwordRules } from "@/utils/authRules"
import CaptchaField from '@/components/CaptchaField.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const redirectTarget = computed(() => {
  const value = route.query.redirect
  return typeof value === 'string' && value.trim() ? value : ''
})

const formRef = ref<FormInstance>()
const loading = ref(false)
const showPwd = ref(false)
const rememberMe = ref(localStorage.getItem("remembered_user") !== null)

const form = reactive({
  username: rememberMe.value
    ? localStorage.getItem("remembered_user") || ""
    : "",
  password: "",
  captchaCode: '',
  captchaToken: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: "请输入用户名/邮箱", trigger: "blur" },
    { min: 2, message: "用户名/邮箱至少 2 个字符", trigger: "blur" },
    { max: 50, message: "用户名/邮箱不能超过 50 个字符", trigger: "blur" },
  ],
  password: passwordRules,
  captchaCode: [{ required: true, message: '请输入图形验证码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.login(form.username, form.password, { token: form.captchaToken, code: form.captchaCode })

    if (rememberMe.value) {
      localStorage.setItem("remembered_user", form.username)
    } else {
      localStorage.removeItem("remembered_user")
    }

    ElMessage.success("登录成功")
    router.replace(redirectTarget.value || "/")
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || ""
    if (msg.includes("invalid credentials")) {
      ElMessage.error("用户名或密码错误，请重试")
    } else if (
      msg.includes("network") ||
      msg.includes("Network") ||
      msg.includes("connect")
    ) {
      ElMessage.error("网络连接失败，请检查后端服务是否运行")
    } else if (msg) {
      ElMessage.error(msg)
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout>
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      @submit.prevent="handleLogin"
      label-position="top"
      class="auth-form"
    >
      <h2 style="text-align:center;margin-bottom:16px;color:#303133;font-size:22px">
        用户登录
      </h2>

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
          @keyup.enter="handleLogin"
        >
          <template #suffix>
            <el-icon class="pwd-toggle" @click="showPwd = !showPwd">
              <component :is="showPwd ? 'View' : 'Hide'" />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="图形验证码" prop="captchaCode">
        <CaptchaField v-model="form.captchaCode" @challenge="form.captchaToken = $event" @submit="handleLogin" />
      </el-form-item>

      <el-form-item>
        <div class="form-options">
          <el-checkbox v-model="rememberMe" size="small">
            记住用户名/邮箱
          </el-checkbox>
          <span style="font-size:15px;color:rgba(26,26,46,0.45)">
            <router-link
              to="/auth/forgot-password"
              style="color:rgba(26,26,46,0.45);text-decoration:none"
            >
              忘记密码
            </router-link>
            <span style="margin:0 6px;color:rgba(26,26,46,0.25)">|</span>
            <router-link
              to="/auth/register"
              style="color:#0b7d5b;font-weight:500"
            >
              立即注册
            </router-link>
          </span>
        </div>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          :loading="loading"
          size="large"
          class="auth-submit-btn"
          @click="handleLogin"
        >
          {{ loading ? "登录中..." : "登 录" }}
        </el-button>
      </el-form-item>
    </el-form>
  </AuthLayout>
</template>

<style scoped>
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
</style>
