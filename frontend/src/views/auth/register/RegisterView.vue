<script setup lang="ts">
import { onBeforeUnmount, ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { registerWithEmail, sendVerificationCode } from "@/api/auth";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import AuthLayout from "@/components/AuthLayout.vue"
import { passwordRules } from "@/utils/authRules"
import CaptchaField from '@/components/CaptchaField.vue'

const router = useRouter();

const formRef = ref<FormInstance>();
const loading = ref(false);
const showPwd = ref(false);
const showConfirmPwd = ref(false);
const sendingCode = ref(false);
const countdown = ref(0);
let timer: ReturnType<typeof setInterval> | null = null;

const form = reactive({
  username: "",
  email: "",
  verificationCode: "",
  password: "",
  confirmPassword: "",
  captchaCode: '',
  captchaToken: '',
});

const rules: FormRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 2, message: "用户名至少 2 个字符", trigger: "blur" },
    { max: 50, message: "用户名不能超过 50 个字符", trigger: "blur" },
  ],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入有效的邮箱地址", trigger: "blur" },
  ],
  verificationCode: [
    { required: true, message: "请输入验证码", trigger: "blur" },
    { len: 6, message: "验证码为 6 位数字", trigger: "blur" },
  ],
  captchaCode: [{ required: true, message: '请输入图形验证码', trigger: 'blur' }],
  password: passwordRules,
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== form.password) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

async function handleSendCode() {
  const valid = await formRef.value?.validateField('email').catch(() => false)
  if (!valid) return
  sendingCode.value = true;
  try {
    const res = await sendVerificationCode(form.email);
    // Mock 模式下验证码直接返回到前端
    const code = res.data.code;
    if (code) {
      form.verificationCode = code;
      ElMessage.success(`验证码已发送（Mock: ${code}）`);
    } else {
      ElMessage.success("验证码已发送，请检查邮箱");
    }
    startCountdown();
  } catch {
    // handled by interceptor
  } finally {
    sendingCode.value = false;
  }
}

function startCountdown() {
  countdown.value = 60;
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      if (timer) clearInterval(timer);
      timer = null;
    }
  }, 1000);
}

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

async function handleRegister() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true;
  try {
    await registerWithEmail({
      username: form.username.trim(),
      password: form.password,
      email: form.email,
      verification_code: form.verificationCode,
      captcha_token: form.captchaToken,
      captcha_code: form.captchaCode,
    });
    ElMessage.success("注册成功，请登录");
    router.push("/auth/login");
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "";
    if (msg.includes("already exists")) {
      ElMessage.error("用户名已存在");
    } else if (msg.includes("验证码")) {
      ElMessage.error(msg);
    } else if (
      msg.includes("network") ||
      msg.includes("Network") ||
      msg.includes("connect")
    ) {
      ElMessage.error("网络连接失败，请检查后端服务是否运行");
    } else if (msg) {
      ElMessage.error(msg);
    }
  } finally {
    loading.value = false;
  }
}

</script>

<template>
  <AuthLayout>
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      @submit.prevent="handleRegister"
      label-position="top"
      class="auth-form"
    >
      <h2 style="text-align:center;margin-bottom:16px;color:#303133;font-size:22px">
        用户注册
      </h2>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="'User'"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱地址"
              size="large"
              :prefix-icon="'Message'"
              clearable
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              :type="showPwd ? 'text' : 'password'"
              placeholder="至少 6 个字符"
              size="large"
              :prefix-icon="'Lock'"
            >
              <template #suffix>
                <el-icon class="pwd-toggle" @click="showPwd = !showPwd">
                  <component :is="showPwd ? 'View' : 'Hide'" />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              :type="showConfirmPwd ? 'text' : 'password'"
              placeholder="再次输入密码"
              size="large"
              :prefix-icon="'Lock'"
            >
              <template #suffix>
                <el-icon class="pwd-toggle" @click="showConfirmPwd = !showConfirmPwd">
                  <component :is="showConfirmPwd ? 'View' : 'Hide'" />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="验证码" prop="verificationCode">
        <div style="display:flex;gap:8px;width:100%">
          <el-input
            v-model="form.verificationCode"
            placeholder="6 位验证码"
            size="large"
            maxlength="6"
            style="flex:1"
          />
          <el-button
            size="large"
            :disabled="countdown > 0 || sendingCode"
            :loading="sendingCode"
            class="code-btn"
            @click="handleSendCode"
          >
            {{ countdown > 0 ? `${countdown}s 后重新发送` : "获取验证码" }}
          </el-button>
        </div>
      </el-form-item>

      <el-form-item label="图形验证码" prop="captchaCode">
        <CaptchaField v-model="form.captchaCode" @challenge="form.captchaToken = $event" @submit="handleRegister" />
      </el-form-item>

      <div style="text-align:center;margin:8px 0 12px">
        <span style="font-size:14px;color:rgba(26,26,46,0.45)">
          已有账号？
          <router-link to="/auth/login" style="color:#0b7d5b;font-weight:500">
            去登录
          </router-link>
        </span>
      </div>

      <el-form-item>
        <el-button
          type="primary"
          :loading="loading"
          size="large"
          class="auth-submit-btn"
          @click="handleRegister"
        >
          {{ loading ? "注册中..." : "注 册" }}
        </el-button>
      </el-form-item>
    </el-form>
  </AuthLayout>
</template>

<style scoped>
.code-btn {
  height: 40px;
  font-size: 13px;
  border-radius: 8px;
  white-space: nowrap;
}
</style>
