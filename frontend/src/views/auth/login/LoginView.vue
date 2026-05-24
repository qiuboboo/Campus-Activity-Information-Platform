<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { getCaptcha } from "@/api/auth"
import { ElMessage } from "element-plus"
import type { FormInstance, FormRules } from "element-plus"
import AuthLayout from "@/components/AuthLayout.vue"
import { passwordRules } from "@/utils/authRules"

const auth = useAuthStore()
const router = useRouter()

const formRef = ref<FormInstance>()
const loading = ref(false)
const showPwd = ref(false)
const rememberMe = ref(localStorage.getItem("remembered_user") !== null)

const captchaToken = ref("")
const captchaImageUrl = ref("")
const captchaLoading = ref(false)

const form = reactive({
  username: rememberMe.value
    ? localStorage.getItem("remembered_user") || ""
    : "",
  password: "",
  captchaCode: "",
})

const rules: FormRules = {
  username: [
    { required: true, message: "请输入用户名/邮箱", trigger: "blur" },
    { min: 2, message: "用户名/邮箱至少 2 个字符", trigger: "blur" },
    { max: 50, message: "用户名/邮箱不能超过 50 个字符", trigger: "blur" },
  ],
  password: passwordRules,
  captchaCode: [
    { required: true, message: "请输入验证码", trigger: "blur" },
  ],
}

async function refreshCaptcha() {
  captchaLoading.value = true
  try {
    const data = await getCaptcha()
    captchaToken.value = data.captchaToken
    captchaImageUrl.value = data.imageUrl
  } catch {
    ElMessage.error("验证码加载失败")
  } finally {
    captchaLoading.value = false
  }
}

onMounted(() => {
  refreshCaptcha()
})

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.login(form.username, form.password, captchaToken.value, form.captchaCode)

    if (rememberMe.value) {
      localStorage.setItem("remembered_user", form.username)
    } else {
      localStorage.removeItem("remembered_user")
    }

    ElMessage.success("登录成功")
    router.replace("/")
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || ""
    if (msg.includes("invalid credentials")) {
      ElMessage.error("用户名或密码错误，请重试")
    } else if (msg.includes("captcha") || msg.includes("验证码")) {
      ElMessage.error(msg)
      refreshCaptcha()
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

      <el-form-item label="验证码" prop="captchaCode">
        <div class="captcha-row">
          <el-input
            v-model="form.captchaCode"
            placeholder="请输入验证码"
            size="large"
            maxlength="6"
            class="captcha-input"
            @keyup.enter="handleLogin"
          />
          <div class="captcha-img-wrap" @click="refreshCaptcha" :class="{ loading: captchaLoading }">
            <img
              v-if="captchaImageUrl"
              :src="captchaImageUrl"
              alt="验证码"
              class="captcha-img"
            />
            <el-icon v-else class="captcha-placeholder"><PictureFilled /></el-icon>
          </div>
        </div>
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
.captcha-row {
  display: flex;
  gap: 12px;
  align-items: center;
  width: 100%;
}

.captcha-input {
  flex: 1;
}

.captcha-img-wrap {
  width: 120px;
  height: 40px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  flex-shrink: 0;
  transition: border-color 0.2s;
}

.captcha-img-wrap:hover {
  border-color: #0b7d5b;
}

.captcha-img-wrap.loading {
  opacity: 0.5;
  pointer-events: none;
}

.captcha-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.captcha-placeholder {
  font-size: 24px;
  color: #c0c4cc;
}

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
