<script setup lang="ts">
import { ref } from 'vue'
import { Document } from '@element-plus/icons-vue'

const props = defineProps<{ activityId: number; title: string }>()

const open = ref(false)
const loading = ref(false)
const error = ref('')
const htmlContent = ref('')

async function loadPoster() {
  if (htmlContent.value) { open.value = true; return }
  loading.value = true
  error.value = ''
  try {
    const resp = await fetch(`/api/activities/${props.activityId}/poster-html`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    htmlContent.value = await resp.text()
  } catch (e: any) {
    error.value = '海报加载失败: ' + (e.message || '网络错误')
  } finally { loading.value = false }
}

async function show() {
  open.value = true
  await loadPoster()
}

function printPoster() {
  const w = window.open('', '_blank', 'width=600,height=700')
  if (w) { w.document.write(htmlContent.value); w.document.close(); w.print() }
  else { window.open(`/api/activities/${props.activityId}/poster-html`, '_blank')?.print() }
}
</script>

<template>
  <el-button @click="show"><el-icon><Document /></el-icon> 查看海报</el-button>

  <el-dialog v-model="open" :title="title + ' — 海报预览'" width="min(92vw, 600px)" destroy-on-close>
    <div v-if="loading" class="preview-loading"><el-skeleton :rows="8" animated /></div>
    <div v-else-if="error" class="preview-error"><el-result icon="error" :sub-title="error"><template #extra><el-button @click="loadPoster">重试</el-button></template></el-result></div>
    <iframe v-else :srcdoc="htmlContent" class="preview-iframe" title="活动海报" />
    <template #footer>
      <el-button @click="printPoster" :disabled="!htmlContent">打印</el-button>
      <el-button type="primary" @click="open = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.preview-iframe { width: 100%; height: 70vh; border: 1px solid #e8f2ea; border-radius: 12px; }
.preview-loading { padding: 24px; }
.preview-error { padding: 24px; }
</style>
