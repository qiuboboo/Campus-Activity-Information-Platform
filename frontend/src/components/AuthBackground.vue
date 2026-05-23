<template>
  <div class="auth-bg"></div>
  <div class="auth-overlay"></div>
</template>

<style scoped>
.auth-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: url("@/assets/huaishitang.jpg") center / cover no-repeat;
}

.auth-overlay {
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
</style>