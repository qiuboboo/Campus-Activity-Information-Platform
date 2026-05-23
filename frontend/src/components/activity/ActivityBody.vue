<script setup lang="ts">
interface Props {
  rawText: string
  attachments: Array<{ url: string; name: string }>
}

defineProps<Props>()
</script>

<template>
  <section class="activity-body">
    <article class="content-card">
      <h2>活动内容</h2>
      <p class="body-text">{{ rawText || '暂无正文内容' }}</p>
    </article>

    <article class="content-card">
      <h2>附件与海报</h2>
      <div v-if="attachments.length > 0" class="attachment-list">
        <a v-for="item in attachments" :key="item.name" :href="item.url" target="_blank" rel="noreferrer">
          {{ item.name }}
        </a>
      </div>
      <el-empty v-else description="暂无附件" :image-size="80" />
    </article>
  </section>
</template>

<style scoped>
.activity-body {
  display: grid;
  gap: 16px;
}

.content-card {
  background: #fff;
  border: 1px solid #edf2ef;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 8px 22px rgba(19, 59, 42, 0.05);
}

.content-card h2 {
  margin: 0 0 14px;
  color: #133b2a;
  font-size: 18px;
}

.body-text {
  margin: 0;
  color: #37423e;
  line-height: 1.9;
  white-space: pre-wrap;
}

.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.attachment-list a {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid #d6e5da;
  color: #0d5e3c;
  text-decoration: none;
  background: #f7fbf8;
}
</style>
