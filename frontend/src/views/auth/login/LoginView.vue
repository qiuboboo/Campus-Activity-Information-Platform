<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

const auth = useAuthStore();
const router = useRouter();

const formRef = ref<FormInstance>();
const loading = ref(false);
const showPwd = ref(false);
const rememberMe = ref(localStorage.getItem("remembered_user") !== null);

const form = reactive({
  username: rememberMe.value
    ? localStorage.getItem("remembered_user") || ""
    : "",
  password: "",
});

const rules: FormRules = {
  username: [{ required: true, message: "请输入用户名/邮箱", trigger: "blur" }],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码至少 6 个字符", trigger: "blur" },
  ],
};

async function handleLogin() {
  if (!form.username.trim()) {
    ElMessage.warning("请输入用户名/邮箱");
    return;
  }
  if (!form.password) {
    ElMessage.warning("请输入密码");
    return;
  }

  loading.value = true;
  try {
    await auth.login(form.username, form.password);

    if (rememberMe.value) {
      localStorage.setItem("remembered_user", form.username);
    } else {
      localStorage.removeItem("remembered_user");
    }

    ElMessage.success("登录成功");
    router.replace("/");
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "";
    if (msg.includes("invalid credentials")) {
      ElMessage.error("用户名或密码错误，请重试");
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

function goHome() {
  router.push("/");
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-bg"></div>
    <div class="login-overlay"></div>

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
        @submit.prevent="handleLogin"
        label-position="top"
        class="login-form"
      >
        <h2
          style="
            text-align: center;
            margin-bottom: 16px;
            color: #303133;
            font-size: 22px;
          "
        >
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

        <el-form-item>
          <div class="form-options">
            <el-checkbox v-model="rememberMe" size="small"
              >记住用户名/邮箱</el-checkbox
            >
            <span style="font-size: 15px; color: rgba(26, 26, 46, 0.45)">
              <router-link
                to="/auth/forgot-password"
                style="color: rgba(26, 26, 46, 0.45); text-decoration: none"
                >忘记密码</router-link
              >
              <span style="margin: 0 6px; color: rgba(26, 26, 46, 0.25)"
                >|</span
              >
              <router-link
                to="/auth/register"
                style="color: #0b7d5b; font-weight: 500"
                >立即注册</router-link
              >
            </span>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            size="large"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? "登录中..." : "登 录" }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  padding-top: 40px;
}
.login-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: url("@/assets/huaishitang.jpg") center / cover no-repeat;
}
.login-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(
    135deg,
    rgba(0, 0, 0, 0.45) 0%,
    rgba(0, 0, 0, 0.25) 50%,
    rgba(0, 0, 0, 0.4) 100%
  );
}
.back-home {
  position: absolute;
  top: 20px;
  left: 24px;
  z-index: 3;
}
.back-home-btn {
  color: rgba(255, 255, 255, 0.85) !important;
  font-size: 16px;
  background: transparent !important;
}
.back-home-btn:hover {
  background: transparent !important;
}
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
.half-transparent-card {
  position: relative;
  z-index: 2;
  width: min(600px, 92vw);
  padding: 32px 40px 28px;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
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
.login-form {
  width: 100%;
}
.login-form :deep(.el-form-item) {
  margin-bottom: 14px;
}
.login-form :deep(.el-form-item__label) {
  color: rgba(26, 26, 46, 0.65);
  font-size: 13px;
  font-weight: 500;
  padding-bottom: 4px;
}
.login-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(26, 26, 46, 0.1);
  border-radius: 10px;
  box-shadow: none;
  transition: all 0.25s ease;
}
.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(11, 125, 91, 0.4);
  background: rgba(255, 255, 255, 0.9);
}
.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #0b7d5b;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(11, 125, 91, 0.15);
}
.login-form :deep(.el-input__inner) {
  color: #1a1a2e;
}
.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(26, 26, 46, 0.3);
}
.login-form :deep(.el-input__prefix) {
  color: rgba(26, 26, 46, 0.35);
}
.login-form :deep(.pwd-toggle) {
  font-size: 22px;
  color: rgba(26, 26, 46, 0.35);
  cursor: pointer;
  border-radius: 6px;
  padding: 4px;
  transition: all 0.2s ease;
}
.login-form :deep(.pwd-toggle:hover) {
  color: #0b7d5b;
  background: rgba(11, 125, 91, 0.08);
}
.login-form :deep(.el-form-item.is-error .el-input__wrapper) {
  border-color: #f56c6c;
  box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.12);
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
}
.login-btn:hover {
  background: linear-gradient(135deg, #0ea36f, #22c98a);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(11, 125, 91, 0.35);
}
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
  .half-transparent-card {
    padding: 24px 20px 20px;
    width: 92vw;
  }
  .el-row :deep(.el-col) {
    width: 100% !important;
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
  .half-transparent-card {
    padding: 24px 18px 20px;
  }
  .login-btn {
    height: 44px;
    font-size: 15px;
  }
}
</style>
