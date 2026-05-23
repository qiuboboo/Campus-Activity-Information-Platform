<script setup lang="ts">
interface Props {
  tags: string[]
  registrations: number
  createdAt: string
}

defineProps<Props>()
</script>

<template>
  <aside class="activity-meta">
    <section class="meta-card">
      <h3>活动标签</h3>
      <div class="tag-list">
        <el-tag v-for="tag in tags" :key="tag" effect="plain" round>
          {{ tag }}
        </el-tag>
      </div>
    </section>

    <section class="meta-card">
      <h3>统计信息</h3>
      <div class="stat-list">
        <div class="stat-item">
          <span class="label">报名人数</span>
          <strong>{{ registrations }}</strong>
        </div>
        <div class="stat-item">
          <span class="label">创建时间</span>
          <strong>{{ createdAt }}</strong>
        </div>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.activity-meta {
  display: grid;
  gap: 16px;
}

.meta-card {
  background: #fff;
  border: 1px solid #edf2ef;
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 8px 22px rgba(19, 59, 42, 0.05);
}

.meta-card h3 {
  margin: 0 0 14px;
  font-size: 16px;
  color: #133b2a;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stat-list {
  display: grid;
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #4d5b55;
  font-size: 13px;
}

.label {
  color: #6b7671;
}

strong {
  color: #133b2a;
  font-size: 15px;
}
</style>
