<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDataSource, createDataSource, updateDataSource } from '@/api/datasources'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const isEdit = ref(false)

const form = ref({
  name: '',
  base_url: '',
  list_selector: '',
  content_selector: '',
  source_level: 'internal',
  owner: '',
  notes: '',
  allowed_domains: '',
  request_interval: 3,
  enabled: true,
  crawl_mode: 'async',
})

const loading = ref(false)
const saving = ref(false)

async function fetchData() {
  if (!route.params.id) return
  isEdit.value = true
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await getDataSource(id)
    const item = res.data
    form.value.name = item.name || ''
    form.value.base_url = item.base_url || ''
    form.value.list_selector = item.list_selector || ''
    form.value.content_selector = item.content_selector || ''
    form.value.source_level = item.source_level || 'internal'
    form.value.owner = item.owner || ''
    form.value.notes = item.notes || ''
    form.value.allowed_domains = item.allowed_domains || ''
    form.value.request_interval = item.request_interval || 3
    form.value.enabled = item.enabled !== false
    form.value.crawl_mode = item.crawl_mode || 'async'
  } catch {
    ElMessage.error('获取数据源信息失败')
    router.push('/datasources')
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!form.value.name) {
    ElMessage.warning('名称不能为空')
    return
  }
  if (!form.value.base_url) {
    ElMessage.warning('地址不能为空')
    return
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      ...form.value,
    }
    if (!payload.allowed_domains) payload.allowed_domains = undefined
    if (!payload.owner) payload.owner = undefined
    if (!payload.notes) payload.notes = undefined
    if (!payload.list_selector) payload.list_selector = undefined
    if (!payload.content_selector) payload.content_selector = undefined

    if (isEdit.value) {
      await updateDataSource(Number(route.params.id), payload)
      ElMessage.success('数据源更新成功')
    } else {
      await createDataSource(payload)
      ElMessage.success('数据源创建成功')
    }
    router.push('/datasources')
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
    <el-button text type="primary" @click="router.push('/datasources')" style="margin-bottom: 12px;">
      <el-icon><ArrowLeft /></el-icon> 返回数据源列表
    </el-button>

    <el-card shadow="hover" style="border-radius: 8px; max-width: 800px;">
      <template #header>
        <span style="font-weight: bold; color: #303133; font-size: 16px;">
          {{ isEdit ? '编辑数据源' : '新建数据源' }}
        </span>
      </template>

      <el-form :model="form" label-position="top">
        <el-form-item label="名称 *" required>
          <el-input v-model="form.name" placeholder="数据源名称，如：学校官网" />
        </el-form-item>

        <el-form-item label="地址 *" required>
          <el-input v-model="form.base_url" placeholder="https://www.example.edu.cn" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="列表页选择器">
              <el-input v-model="form.list_selector" placeholder="CSS 选择器，如 .event-list a" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="详情页选择器">
              <el-input v-model="form.content_selector" placeholder="CSS 选择器，如 .content" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="来源级别">
              <el-select v-model="form.source_level" style="width: 100%">
                <el-option label="官方" value="official" />
                <el-option label="校内" value="internal" />
                <el-option label="校外" value="external" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="抓取模式">
              <el-select v-model="form.crawl_mode" style="width: 100%">
                <el-option label="异步（默认）" value="async" />
                <el-option label="同步（调试）" value="sync" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="请求间隔（秒）">
              <el-input-number v-model="form.request_interval" :min="1" :max="30" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="所属组织/单位">
          <el-input v-model="form.owner" placeholder="如：校团委、计算机学院" />
        </el-form-item>

        <el-form-item label="允许的域名">
          <el-input v-model="form.allowed_domains" placeholder="逗号分隔，如：example.edu.cn, sysu.edu.cn" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>

        <el-form-item>
          <el-switch v-model="form.enabled" active-text="启用" inactive-text="停用" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSubmit" size="large">
            {{ isEdit ? '保存修改' : '创建数据源' }}
          </el-button>
          <el-button @click="router.push('/datasources')" size="large">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
