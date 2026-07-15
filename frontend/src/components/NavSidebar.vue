<template>
  <aside class="side-left">
    <nav class="side-nav">
      <button
        v-for="item in navItems"
        :key="item.key"
        type="button"
        class="side-nav-item"
        :class="{ active: activeNav === item.key }"
        @click="$emit('selectNav', item.key)"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div class="side-divider"></div>
    <div class="side-section-title">分类入口</div>
    <div class="side-categories">
      <button
        v-for="cat in activityTypeList.slice(0, 6)"
        :key="cat"
        type="button"
        class="side-cat-item"
        :class="{ active: selectedCategoryId === cat }"
        @click="$emit('selectCategory', cat)"
      >
        <span class="side-cat-dot"></span>
        <span>{{ cat }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { Grid, TrendCharts, Collection, Star, Plus } from '@element-plus/icons-vue'

const navItems = [
  { key: 'all', label: '全部活动', icon: Grid },
  { key: 'hot', label: '热门推荐', icon: TrendCharts },
  { key: 'categories', label: '按类别', icon: Collection },
  { key: 'my', label: '我的活动', icon: Star },
  { key: 'create', label: '创建活动', icon: Plus },
]

defineProps<{
  activeNav: string
  activityTypeList: string[]
  selectedCategoryId: string | null
}>()

defineEmits<{
  (e: 'selectNav', key: string): void
  (e: 'selectCategory', cat: string): void
}>()
</script>

<style scoped>
.side-left {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 160px;
  background: #f0f9f4;
  overflow-y: auto;
  padding-top: 104px;
  z-index: 1;
  border-right: 1px solid #d0ede0;
}

.side-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 8px;
}

.side-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  transition: all 0.2s;
  border: 0;
  background: transparent;
  width: 100%;
  text-align: left;
}

.side-nav-item:hover {
  background: #f0f9f4;
  color: #0d5e3c;
}

.side-nav-item.active {
  background: #e8f5e9;
  color: #0d5e3c;
  font-weight: 700;
}

.side-nav-item .el-icon {
  font-size: 18px;
}

.side-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 12px 16px;
}

.side-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #b0b0b0;
  padding: 0 16px 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.side-categories {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 8px;
}

.side-cat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: all 0.2s;
  border: 0;
  background: transparent;
  width: 100%;
  text-align: left;
}

.side-cat-item:hover {
  background: #f0f9f4;
  color: #0d5e3c;
}

.side-cat-item.active {
  background: #e8f5e9;
  color: #0d5e3c;
  font-weight: 600;
}

.side-cat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #27a66b;
}

@media (max-width: 768px) {
  .side-left { display: none; }
}
</style>
