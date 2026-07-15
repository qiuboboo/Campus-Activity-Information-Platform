<script setup lang="ts">
import { computed } from 'vue'
import type { Attachment } from '@/api/activities'
import { safeAttachmentUrl } from '@/utils/attachments'

interface Props {
  rawText: string
  contentHtml?: string | null
  attachments: Attachment[]
}

const props = defineProps<Props>()

function sanitizeHtml(value?: string | null) {
  if (!value || typeof window === 'undefined') return ''
  const doc = new DOMParser().parseFromString(value, 'text/html')
  doc.querySelectorAll('script, iframe, object, embed, link, style').forEach((node) => node.remove())
  doc.body.querySelectorAll('*').forEach((node) => {
    for (const attr of [...node.attributes]) {
      const name = attr.name.toLowerCase()
      const attrValue = attr.value.trim().toLowerCase()
      if (name.startsWith('on') || attrValue.startsWith('javascript:')) node.removeAttribute(attr.name)
    }
  })
  return doc.body.innerHTML
}

const safeContentHtml = computed(() => sanitizeHtml(props.contentHtml))
</script>

<template>
  <section class="activity-body">
    <article class="content-card">
      <h2>活动内容</h2>
      <div v-if="safeContentHtml" class="body-html" v-html="safeContentHtml"></div>
      <p v-else class="body-text">{{ rawText || '暂无正文内容' }}</p>
    </article>

    <article class="content-card">
      <h2>附件与海报</h2>
      <div v-if="attachments.length > 0" class="attachment-list">
        <template v-for="item in attachments" :key="item.id || `${item.name}-${item.url}`">
          <a v-if="safeAttachmentUrl(item.url)" :href="safeAttachmentUrl(item.url)!" target="_blank" rel="noopener noreferrer">
            {{ item.name }}
          </a>
          <span v-else class="attachment-unavailable">{{ item.name }}（附件地址不可用）</span>
        </template>
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

.body-html {
  color: #37423e;
  line-height: 1.9;
  margin-bottom: 16px;
}

.body-html :deep(h1),
.body-html :deep(h2),
.body-html :deep(h3) {
  color: #133b2a;
}

.body-html :deep(p) {
  margin: 0 0 10px;
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

.attachment-unavailable { color: #8b5e24; font-size: 14px; }
</style>
