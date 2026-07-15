<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getCaptcha } from '@/api/auth'

const model = defineModel<string>({ default: '' })
const emit = defineEmits<{ challenge: [token: string]; submit: [] }>()
const imageUrl = ref('')
const loading = ref(false)

function disposeImage() {
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
  imageUrl.value = ''
}

async function refresh() {
  loading.value = true
  try {
    disposeImage()
    const challenge = await getCaptcha()
    imageUrl.value = challenge.imageUrl
    model.value = ''
    emit('challenge', challenge.token)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '验证码加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
onBeforeUnmount(disposeImage)
defineExpose({ refresh })
</script>

<template>
  <div class="captcha-field">
    <el-input v-model="model" inputmode="numeric" maxlength="6" placeholder="请输入图形验证码" @keyup.enter="emit('submit')" />
    <button class="captcha-image" type="button" :disabled="loading" title="点击更换验证码" @click="refresh">
      <img v-if="imageUrl" :src="imageUrl" alt="图形验证码，点击可更换" />
      <span v-else>{{ loading ? '加载中' : '重试' }}</span>
    </button>
  </div>
</template>

<style scoped>
.captcha-field { display: flex; align-items: stretch; gap: 8px; width: 100%; }
.captcha-image { width: 116px; min-width: 116px; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: #f8fbf9; cursor: pointer; padding: 0; }
.captcha-image:disabled { cursor: wait; }
.captcha-image img { display: block; width: 100%; height: 38px; object-fit: cover; }
</style>
