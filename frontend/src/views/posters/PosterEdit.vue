<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPoster, updatePoster, submitPoster } from '@/api/posters'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const form = ref({
  title: '',
  raw_text: '',
  summary: '',
  event_time: '',
  location: '',
  organizer: '',
  source_type: 'manual',
  source_url: '',
  tags: '',
  activity_type: '',
})

const loading = ref(true)
const saving = ref(false)

async function fetchData() {
  try {
    const id = Number(route.params.id)
    const res = await getPoster(id)
    const item = res.data.item
    form.value.title = item.title || ''
    form.value.raw_text = item.raw_text || ''
    form.value.summary = item.summary || ''
    form.value.event_time = item.event_time || ''
    form.value.location = item.location || ''
    form.value.organizer = item.organizer || ''
    form.value.source_type = item.source_type || 'manual'
    form.value.source_url = item.source_url || ''
    form.value.tags = item.tags || ''
    form.value.activity_type = item.activity_type || ''
  } catch {
    ElMessage.error('获取海报信息失败')
    router.push('/posters')
  } finally {
    loading.value = false
  }
}

async function handleSave(as: 'draft' | 'pending_review' = 'draft') {
  if (!form.value.title) {
    ElMessage.warning('标题不能为空')
    return
  }
  saving.value = true
  try {
    const id = Number(route.params.id)
    const payload: Record<string, unknown> = { ...form.value }
    if (payload.event_time) {
      payload.event_time = new Date(payload.event_time as string).toISOString()
    } else {
      delete payload.event_time
    }
    if (!payload.source_url) payload.source_url = undefined
    if (!payload.tags) payload.tags = undefined
    if (!payload.activity_type) payload.activity_type = undefined
    payload.status = as

    await updatePoster(id, payload)

    if (as === 'pending_review') {
      await submitPoster(id)
    }

    ElMessage.success(as === 'pending_review' ? '已保存并提交审核' : '已保存')
    router.push(`/posters/${id}`)
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div v-loading="loading">
    <el-button text type="primary" @click="router.push(`/posters/${route.params.id}`)" style="margin-bottom: 12px;">
      <el-icon><ArrowLeft /></el-icon> 返回详情
    </el-button>

    <el-card shadow="hover" style="border-radius: 8px; max-width: 800px;">
      <template #header>
        <span style="font-weight: bold; color: #303133; font-size: 16px;">编辑活动海报</span>
      </template>

      <el-form :model="form" label-position="top">
        <el-form-item label="标题 *" required>
          <el-input v-model="form.title" placeholder="活动标题" />
        </el-form-item>

        <el-form-item label="活动原文">
          <el-input
            v-model="form.raw_text"
            type="textarea"
            :rows="4"
            placeholder="活动原文（AI提取用）"
          />
        </el-form-item>

        <el-row :gutter="16">
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
          <el-col :span="12">
            <el-form-item label="地点">
              <el-input v-model="form.location" placeholder="活动地点" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="主办方">
              <el-input v-model="form.organizer" placeholder="主办方/组织者" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="活动类型">
              <el-input v-model="form.activity_type" placeholder="如：讲座、比赛、展览" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="摘要">
          <el-input
            v-model="form.summary"
            type="textarea"
            :rows="2"
            placeholder="活动摘要"
          />
        </el-form-item>

        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="逗号分隔的标签" />
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
          <el-button type="primary" :loading="saving" @click="handleSave('draft')" size="large">
            保存修改
          </el-button>
          <el-button
            v-if="auth.isPublisher"
            :loading="saving"
            @click="handleSave('pending_review')"
            size="large"
            type="success"
          >
            保存并提交审核
          </el-button>
          <el-button @click="router.push(`/posters/${route.params.id}`)" size="large">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
