<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import ActivityCover from '@/components/ActivityCover.vue'
import { createActivity, getActivityById, submitActivityForReview, updateActivity, type ActivityForm, type Attachment } from '@/api/activities'
import { deleteUpload, uploadAttachment } from '@/api/uploads'
import { ACCEPTED_ATTACHMENT_EXTENSIONS, MAX_ATTACHMENT_SIZE, validateAttachmentFile } from '@/utils/attachments'

const route = useRoute()
const router = useRouter()
const editing = computed(() => Boolean(route.params.id))
const id = computed(() => Number(route.params.id))
const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const loaded = ref(!editing.value)
const dirty = ref(false)
const tagsText = ref('')
const rejectReason = ref('')
const uploading = ref(false)
const failedUploads = ref<Array<{ file: File; message: string }>>([])
const coverUploading = ref(false)

const COVER_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
const COVER_IMAGE_EXTENSIONS = '.jpg,.jpeg,.png,.webp,.gif'

const form = reactive<ActivityForm>({
  title: '',
  summary: '',
  raw_text: '',
  event_time: null,
  location: '',
  organizer: '',
  activity_type: '',
  tags: [],
  attachments: [],
  cover_image_url: '',
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入活动标题', trigger: 'blur' }],
  raw_text: [{ required: true, message: '请输入活动内容', trigger: 'blur' }],
  activity_type: [{ required: true, message: '请选择活动分类', trigger: 'change' }],
}

function assign(value: Partial<ActivityForm> & { reject_reason?: string }) {
  Object.assign(form, value, {
    tags: value.tags || [],
    attachments: (value.attachments || []).filter((attachment) => Boolean(attachment.id)),
    cover_image_url: value.cover_image_url || '',
  })
  tagsText.value = (value.tags || []).join('、')
  rejectReason.value = value.reject_reason || ''
}

async function load() {
  if (!editing.value) return
  loading.value = true
  try {
    const { data } = await getActivityById(id.value)
    assign(data)
  } catch {
    router.replace('/my/activities')
  } finally {
    loaded.value = true
    loading.value = false
  }
}

async function addAttachment(file: File) {
  const invalid = validateAttachmentFile(file)
  if (invalid) {
    ElMessage.warning(invalid)
    return
  }
  uploading.value = true
  try {
    const { data } = await uploadAttachment(file)
    form.attachments.push(data)
    dirty.value = true
    ElMessage.success(`“${data.name}”已上传`)
  } catch (error: any) {
    failedUploads.value.push({ file, message: error?.response?.data?.message || '附件上传失败' })
  } finally {
    uploading.value = false
  }
}

function selectAttachment(uploadFile: { raw?: File }) {
  if (uploadFile.raw) void addAttachment(uploadFile.raw)
}

async function uploadCover(file: File) {
  if (!COVER_IMAGE_TYPES.has(file.type)) {
    ElMessage.warning('封面仅支持 JPG、PNG、WEBP 或 GIF 图片')
    return
  }
  if (file.size > MAX_ATTACHMENT_SIZE) {
    ElMessage.warning('封面图片不能超过 10 MB')
    return
  }
  coverUploading.value = true
  try {
    const { data } = await uploadAttachment(file)
    form.cover_image_url = data.url
    dirty.value = true
    ElMessage.success('封面已上传')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || '封面上传失败')
  } finally {
    coverUploading.value = false
  }
}

function selectCover(uploadFile: { raw?: File }) {
  if (uploadFile.raw) void uploadCover(uploadFile.raw)
}

async function retryUpload(file: File) {
  failedUploads.value = failedUploads.value.filter((item) => item.file !== file)
  await addAttachment(file)
}

async function removeAttachment(attachment: Attachment, index: number) {
  try {
    await ElMessageBox.confirm(`确定移除“${attachment.name}”吗？`, '移除附件', { type: 'warning' })
    if (attachment.id) await deleteUpload(attachment.id)
    form.attachments.splice(index, 1)
    dirty.value = true
    ElMessage.success('附件已移除')
  } catch {}
}

async function save(submit = false) {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  form.tags = tagsText.value.split(/[、,，]/).map((item) => item.trim()).filter(Boolean)
  try {
    const data = editing.value ? (await updateActivity(id.value, form)).data : (await createActivity(form)).data
    if (submit) await submitActivityForReview(data.id)
    dirty.value = false
    ElMessage.success(submit ? '已提交审核' : '草稿已保存')
    router.push('/my/activities')
  } catch {
  } finally {
    saving.value = false
  }
}

onMounted(load)
watch(id, () => {
  if (editing.value) {
    loaded.value = false
    dirty.value = false
    load()
  }
})

onBeforeRouteLeave(async () => {
  if (!dirty.value) return true
  try {
    await ElMessageBox.confirm('尚有未保存修改，确定离开？', '未保存内容', { type: 'warning' })
    return true
  } catch {
    return false
  }
})
</script>

<template>
  <AppShell :title="editing ? '编辑活动' : '创建活动'">
    <PageState :loading="loading" :empty="!loaded" empty-text="活动不存在">
      <section v-if="loaded" class="surface-card editor">
        <el-alert
          v-if="rejectReason"
          title="该活动曾被驳回"
          type="warning"
          :description="`驳回原因：${rejectReason}`"
          :closable="false"
          show-icon
          class="reject-alert"
        />

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @change="dirty = true">
          <el-row :gutter="16">
            <el-col :md="16">
              <el-form-item label="活动标题" prop="title"><el-input v-model="form.title" maxlength="100" show-word-limit /></el-form-item>
            </el-col>
            <el-col :md="8">
              <el-form-item label="活动类型" prop="activity_type">
                <el-select v-model="form.activity_type" placeholder="选择分类" style="width:100%">
                  <el-option v-for="item in ['讲座','晚会','竞赛','论坛','展览','招聘','体育','其他']" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="活动封面">
            <div class="cover-field">
              <div class="cover-controls">
                <el-upload :show-file-list="false" :auto-upload="false" :accept="COVER_IMAGE_EXTENSIONS" :disabled="coverUploading" @change="selectCover">
                  <el-button :loading="coverUploading">上传封面图片</el-button>
                  <template #tip><div class="el-upload__tip">JPG、PNG、WEBP 或 GIF，最大 10 MB;不上传时按分类自动生成封面。</div></template>
                </el-upload>
                <el-input v-model="form.cover_image_url" clearable placeholder="也可直接粘贴图片链接" @change="dirty = true" />
              </div>
              <div class="cover-preview">
                <ActivityCover :src="form.cover_image_url" :category="form.activity_type" alt="活动封面预览" />
              </div>
            </div>
          </el-form-item>

          <el-form-item label="活动摘要"><el-input v-model="form.summary" type="textarea" :rows="2" maxlength="300" show-word-limit /></el-form-item>
          <el-form-item label="活动正文" prop="raw_text"><el-input v-model="form.raw_text" type="textarea" :rows="8" /></el-form-item>

          <el-row :gutter="16">
            <el-col :md="12"><el-form-item label="活动时间"><el-date-picker v-model="form.event_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" /></el-form-item></el-col>
            <el-col :md="12"><el-form-item label="地点"><el-input v-model="form.location" /></el-form-item></el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :md="12"><el-form-item label="主办方"><el-input v-model="form.organizer" /></el-form-item></el-col>
            <el-col :md="12"><el-form-item label="标签（以顿号或逗号分隔）"><el-input v-model="tagsText" /></el-form-item></el-col>
          </el-row>

          <el-form-item label="附件">
            <div class="attachments">
              <el-tag v-for="(file, index) in form.attachments" :key="file.id || file.url" closable @close="removeAttachment(file, index)">{{ file.name }}</el-tag>
            </div>
            <el-upload class="attachment-upload" :show-file-list="false" :auto-upload="false" :accept="ACCEPTED_ATTACHMENT_EXTENSIONS" :disabled="uploading" @change="selectAttachment">
              <el-button :loading="uploading">选择并上传附件</el-button>
              <template #tip><div class="el-upload__tip">支持图片、PDF、Word 和 Excel，单文件最大 10 MB。</div></template>
            </el-upload>
            <div v-for="failed in failedUploads" :key="`${failed.file.name}-${failed.file.lastModified}`" class="upload-failure">
              <span>{{ failed.file.name }}：{{ failed.message }}</span>
              <el-button text type="primary" @click="retryUpload(failed.file)">重试</el-button>
            </div>
          </el-form-item>

          <div class="form-actions">
            <el-button @click="router.back()">取消</el-button>
            <el-button :loading="saving" @click="save(false)">保存草稿</el-button>
            <el-button type="primary" :loading="saving" @click="save(true)">提交审核</el-button>
          </div>
        </el-form>
      </section>
    </PageState>
  </AppShell>
</template>

<style scoped>
.editor { padding: 24px; }
.reject-alert { margin-bottom: 18px; }
.cover-field { display: grid; grid-template-columns: minmax(0, 1fr) 180px; gap: 14px; align-items: start; width: 100%; }
.cover-controls { display: grid; gap: 10px; }
.cover-preview { height: 102px; border-radius: 8px; overflow: hidden; }
.attachments { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.attachment-upload { display: block; }
.upload-failure { display: flex; gap: 8px; align-items: center; margin-top: 8px; color: var(--el-color-danger); }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; }
@media (max-width: 700px) { .editor { padding: 16px; } .cover-field { grid-template-columns: 1fr; } .cover-preview { height: 140px; } }
</style>
