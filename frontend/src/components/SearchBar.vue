<template>
  <div class="nav-search">
    <el-input
      :model-value="searchKeyword"
      @update:model-value="$emit('update:searchKeyword', $event)"
      size="large"
      class="nav-search-input"
      placeholder="搜索活动、主题、地点…"
      clearable
      @keyup.enter="$emit('search')"
    >
      <template #prefix>
        <el-icon class="search-prefix-icon"><Search /></el-icon>
      </template>
    </el-input>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'

defineProps<{ searchKeyword: string }>()
defineEmits<{
  (e: 'update:searchKeyword', v: string): void
  (e: 'search'): void
}>()
</script>

<style scoped>
.nav-search {
  flex: 1;
  max-width: 360px;
  margin: 0 24px;
}

.nav-search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  box-shadow: none;
  padding: 4px 16px;
  transition: background 0.2s;
}

.nav-search-input :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.25);
}

.nav-search-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.3);
}

.nav-search-input :deep(.el-input__inner) {
  color: #fff;
  font-size: 16px;
}

.nav-search-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}

.nav-search-input :deep(.el-input__prefix) {
  color: rgba(255, 255, 255, 0.5);
}

.search-prefix-icon {
  font-size: 16px;
}

@media (max-width: 768px) {
  .nav-search { display: none; }
}
</style>
