<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { coverTheme } from '@/utils/coverColors'
import { safeAttachmentUrl } from '@/utils/attachments'

interface Props {
  src?: string | null
  category?: string | null
  alt?: string
  /** 占位图中间的分类文字,默认显示 */
  showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), { showLabel: true })

const failed = ref(false)
watch(() => props.src, () => { failed.value = false })

const safeSrc = computed(() => safeAttachmentUrl(props.src))
const showImage = computed(() => Boolean(safeSrc.value) && !failed.value)
const theme = computed(() => coverTheme(props.category))
const label = computed(() => (props.category || '').trim() || '活动')
</script>

<template>
  <div class="activity-cover-box">
    <img
      v-if="showImage"
      :src="safeSrc!"
      :alt="alt || label"
      loading="lazy"
      @error="failed = true"
    />
    <div v-else class="cover-placeholder" :style="{ background: theme.gradient }">
      <span v-if="showLabel" class="cover-label">{{ label }}</span>
      <span class="cover-glyph" aria-hidden="true">{{ theme.glyph }}</span>
    </div>
  </div>
</template>

<style scoped>
.activity-cover-box {
  width: 100%;
  height: 100%;
  border-radius: inherit;
  overflow: hidden;
}

.activity-cover-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-placeholder {
  position: relative;
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.cover-label {
  color: #fff;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-shadow: 0 1px 2px rgba(9, 30, 20, 0.35);
  z-index: 1;
}

/* 签名细节: 分类首字作低透明度"铅字"水印,右下出血,信息即装饰 */
.cover-glyph {
  position: absolute;
  right: -0.12em;
  bottom: -0.32em;
  font-size: 5.2em;
  font-weight: 900;
  line-height: 1;
  color: rgba(255, 255, 255, 0.14);
  user-select: none;
  pointer-events: none;
}
</style>
