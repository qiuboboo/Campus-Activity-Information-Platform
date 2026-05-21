<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createPoster } from '@/api/posters'
import { ElMessage } from 'element-plus'

const router = useRouter()

const form = ref({
  title: '',
  raw_text: '',
  summary: '',
  event_time: '',
  location: '',
  organizer: '',
  source_type: 'manual',
  source_url: '',
  status: 'draft',
})

const loading = ref(false)

async function handleSubmit() {
  if (!form.value.raw_text) {
    ElMessage.warning('请输入活动原文')
    return
  }
  loading.value = true
  try {
    const payload: Record<string, unknown> = { ...form.value }
    if (payload.event_time) {
      payload.event_time = new Date(payload.event_time as string).toISOString()
    } else {
      delete payload.event_time
    }
    if (!payload.source_url) payload.source_url = undefined
    const res = await createPoster(payload)
    ElMessage.success('海报创建成功')
    router.push(`/posters/${res.data.item.id}`)
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <el-button text type="primary" @click="router.push('/posters')" style="margin-bottom: 12px;">
      <el-icon><ArrowLeft /></el-icon> 返回列表
    </el-button>

    <el-card shadow="hover" style="border-radius: 8px; max-width: 800px;">
      <template #header>
        <span style="font-weight: bold; color: #303133; font-size: 16px;">创建活动海报</span>
      </template>

      <el-form :model="form" label-position="top">
        <el-form-item label="活动原文 *" required>
          <el-input
            v-model="form.raw_text"
            type="textarea"
            :rows="4"
            placeholder="请输入活动原文，系统将自动提取标题和摘要"
          />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="标题">
              <el-input v-model="form.title" placeholder="不填则从原文自动提取" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="活动时间">
              <el-date-picker
                v-model="form.event_time"
                type="datetime"
                placeholder="选择活动时间"
                style="width: 100%"
                value-format="YYYY-MM-DDTHH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="地点">
              <el-input v-model="form.location" placeholder="活动地点" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主办方">
              <el-input v-model="form.organizer" placeholder="主办方/组织者" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="摘要">
          <el-input
            v-model="form.summary"
            type="textarea"
            :rows="2"
            placeholder="不填则从原文自动提取前120字"
          />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="来源链接">
              <el-input v-model="form.source_url" placeholder="https://..." />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="来源类型">
              <el-select v-model="form.source_type" style="width: 100%">
                <el-option label="手动录入" value="manual" />
                <el-option label="爬虫抓取" value="crawl" />
                <el-option label="AI 生成" value="ai" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit" size="large">
            创建海报
          </el-button>
          <el-button @click="router.push('/posters')" size="large">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
