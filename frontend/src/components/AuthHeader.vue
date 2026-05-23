<template>
    <div class="back-home">
        <el-button @click="goHome" class="back-home-btn">返回首页</el-button>
    </div>

    <div class="top-center-title">
        <h1>逸仙活动云</h1>
        <p class="en-subtitle">Sun Yat-sen University Activity Cloud Platform</p>
    </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script>

<style scoped>
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
}

@media (max-width: 480px) {
  .back-home {
    top: 12px;
    left: 12px;
  }

  .top-center-title h1 {
    font-size: 28px;
  }
}
</style>