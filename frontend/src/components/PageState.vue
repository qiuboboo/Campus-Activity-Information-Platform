<script setup lang="ts">
defineProps<{ loading?: boolean; error?: string; empty?: boolean; emptyText?: string }>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <el-skeleton v-if="loading" animated :rows="6" />
  <el-result v-else-if="error" icon="error" title="加载失败" :sub-title="error">
    <template #extra><el-button type="primary" @click="$emit('retry')">重试</el-button></template>
  </el-result>
  <el-empty v-else-if="empty" :description="emptyText || '暂无数据'" />
  <slot v-else />
</template>
