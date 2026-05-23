<template>
  <div class="auth-wrapper">
    <AuthBackground />
    <AuthHeader />
    <div class="half-transparent-card">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import AuthBackground from './AuthBackground.vue'
import AuthHeader from './AuthHeader.vue'
</script>

<style scoped>
.auth-wrapper {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  padding-top: 40px;
}

.half-transparent-card {
  position: relative;
  z-index: 2;
  width: min(600px, 92vw);
  padding: 32px 36px 28px;
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

/* ---- 共享表单样式 ---- */
.auth-form {
  width: 100%;
}

.auth-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.auth-form :deep(.el-form-item__label) {
  color: rgba(26, 26, 46, 0.65);
  font-size: 13px;
  font-weight: 500;
  padding-bottom: 4px;
}

.auth-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(26, 26, 46, 0.1);
  border-radius: 10px;
  box-shadow: none;
  transition: all 0.25s ease;
}

.auth-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(11, 125, 91, 0.4);
  background: rgba(255, 255, 255, 0.9);
}

.auth-form :deep(.el-input__wrapper.is-focus) {
  border-color: #0b7d5b;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(11, 125, 91, 0.15);
}

.auth-form :deep(.el-input__inner) {
  color: #1a1a2e;
}

.auth-form :deep(.el-input__inner::placeholder) {
  color: rgba(26, 26, 46, 0.3);
}

.auth-form :deep(.el-input__prefix) {
  color: rgba(26, 26, 46, 0.35);
}

.auth-form :deep(.pwd-toggle) {
  font-size: 22px;
  color: rgba(26, 26, 46, 0.35);
  cursor: pointer;
  border-radius: 6px;
  padding: 4px;
  transition: all 0.2s ease;
}

.auth-form :deep(.pwd-toggle:hover) {
  color: #0b7d5b;
  background: rgba(11, 125, 91, 0.08);
}

.auth-form :deep(.el-form-item.is-error .el-input__wrapper) {
  border-color: #f56c6c;
  box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.12);
}

.auth-submit-btn {
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

.auth-submit-btn:hover {
  background: linear-gradient(135deg, #0ea36f, #22c98a);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(11, 125, 91, 0.35);
}

/* ---- 响应式 ---- */
@media (max-width: 768px) {
  .half-transparent-card {
    padding: 24px 20px 20px;
    width: 92vw;
  }

  .el-row :deep(.el-col) {
    width: 100% !important;
  }
}

@media (max-width: 480px) {
  .half-transparent-card {
    padding: 24px 18px 20px;
  }

  .auth-submit-btn {
    height: 44px;
    font-size: 15px;
  }
}
</style>
