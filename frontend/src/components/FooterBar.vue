<template>
  <footer class="home-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="footer-name">逸仙活动云</span>
        <span class="footer-en">Sun Yat-sen University Activity Cloud Platform</span>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© {{ currentYearLabel }} 中山大学 · 校园活动信息平台</p>
    </div>
  </footer>
</template>

<script setup lang="ts">
defineProps<{ currentYearLabel: number }>()
</script>

<style scoped>
.home-footer {
  background: #0a0a0a;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  height: 60px;
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.footer-name {
  font-size: 16px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 1px;
}

.footer-en {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 0.5px;
}

.footer-bottom {
  max-width: 1400px;
  margin: 0 auto;
  padding: 6px 32px 10px;
  text-align: center;
}

.footer-bottom p {
  margin: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  line-height: 1.6;
}

@media (max-width: 768px) {
  .footer-inner { flex-direction: column; gap: 4px; height: auto; padding: 12px 16px; }
  .footer-bottom { padding: 4px 16px 8px; }
}
</style>