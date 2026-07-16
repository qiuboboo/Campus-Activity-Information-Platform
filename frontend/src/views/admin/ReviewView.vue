<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import { bulkReviewActivities, getPosterDuplicates, getReviewActivities, mergePosterSource, rebuildPosterKnowledge, reviewActivity } from '@/api/admin'
import { enrichPosterWithAi } from '@/api/ai'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import type { Activity } from '@/api/activities'

const loading = ref(false)
const error = ref('')
const activities = ref<Activity[]>([])
const selected = ref<Activity[]>([])
const duplicateDialog = ref(false)
const duplicateBase = ref<Activity | null>(null)
const duplicates = ref<Activity[]>([])
const previewDrawer = ref(false)
const previewActivity = ref<Activity | null>(null)

function openPreview(activity: Activity) {
  previewActivity.value = activity
  previewDrawer.value = true
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    activities.value = (await getReviewActivities()).data.items
  } catch (e: any) {
    error.value = e?.response?.data?.message || '审核队列加载失败'
  } finally {
    loading.value = false
  }
}

async function review(id: number, action: 'approve' | 'reject') {
  try {
    const reason = action === 'reject'
      ? await ElMessageBox.prompt('请输入驳回理由', '驳回活动', { inputPattern: /.+/, inputErrorMessage: '驳回理由不能为空' })
      : null
    await reviewActivity(id, action, reason?.value || '')
    ElMessage.success(action === 'approve' ? '已批准' : '已驳回')
    load()
  } catch {}
}

async function bulk(action: 'approve' | 'reject') {
  if (!selected.value.length) return
  try {
    const comment = action === 'reject'
      ? (await ElMessageBox.prompt('请输入批量驳回理由', '批量驳回', { inputPattern: /.+/, inputErrorMessage: '驳回理由不能为空' })).value
      : ''
    await ElMessageBox.confirm(`确认${action === 'approve' ? '批准' : '驳回'} ${selected.value.length} 条活动？`, '批量审核', { type: 'warning' })
    const { data }: any = await bulkReviewActivities(selected.value.map((item) => item.id), action, comment)
    ElMessage.success(`处理完成：成功 ${data.succeeded?.length || 0}，失败 ${data.failed?.length || 0}`)
    load()
  } catch {}
}

async function showDuplicates(activity: Activity) {
  const { data } = await getPosterDuplicates(activity.id)
  duplicateBase.value = data.poster
  duplicates.value = data.duplicates
  duplicateDialog.value = true
}

async function mergeDuplicate(source: Activity) {
  if (!duplicateBase.value) return
  try {
    await ElMessageBox.confirm(`确认把“${source.title}”合并到“${duplicateBase.value.title}”？`, '合并重复活动', { type: 'warning' })
    await mergePosterSource(duplicateBase.value.id, source.id)
    ElMessage.success('已合并')
    duplicateDialog.value = false
    load()
  } catch {}
}

async function rebuild(activity: Activity) {
  await rebuildPosterKnowledge(activity.id)
  ElMessage.success('知识关联已重建')
}

async function enrich(activity: Activity) {
  await enrichPosterWithAi(activity.id)
  ElMessage.success('AI 增强已完成')
  load()
}

onMounted(load)
</script>

<template>
  <AppShell title="审核队列">
    <template #heading>
      <el-button :disabled="!selected.length" @click="bulk('reject')">驳回选中（{{ selected.length }}）</el-button>
      <el-button type="primary" :disabled="!selected.length" @click="bulk('approve')">批准选中（{{ selected.length }}）</el-button>
    </template>

    <PageState :loading="loading" :error="error" :empty="!loading && !error && !activities.length" empty-text="暂无待审核活动" @retry="load">
      <section class="surface-card table-wrap">
        <el-table :data="activities" @selection-change="selected = $event">
          <el-table-column type="selection" width="48" />
          <el-table-column prop="title" label="活动" min-width="210" />
          <el-table-column prop="activity_type" label="分类" width="100" />
          <el-table-column prop="organizer" label="主办方" min-width="130" />
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column label="操作" width="380">
            <template #default="{ row }">
              <el-button text type="primary" @click="openPreview(row)">预览</el-button>
              <el-button text type="success" @click="review(row.id, 'approve')">批准</el-button>
              <el-button text type="danger" @click="review(row.id, 'reject')">驳回</el-button>
              <el-button text type="primary" @click="showDuplicates(row)">查重</el-button>
              <el-button text type="primary" @click="rebuild(row)">知识</el-button>
              <el-button text type="primary" @click="enrich(row)">AI</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </PageState>

    <el-dialog v-model="duplicateDialog" title="重复活动检查" width="min(92vw, 680px)">
      <template v-if="duplicateBase">
        <p class="base-title">当前活动：{{ duplicateBase.title }}</p>
        <el-empty v-if="!duplicates.length" description="未发现重复候选" />
        <article v-for="item in duplicates" v-else :key="item.id" class="duplicate-item">
          <div>
            <strong>{{ item.title }}</strong>
            <span>{{ item.organizer || '未知主办方' }}</span>
          </div>
          <el-button type="primary" text @click="mergeDuplicate(item)">合并到当前活动</el-button>
        </article>
      </template>
    </el-dialog>

    <el-drawer v-model="previewDrawer" size="min(92vw, 580px)" title="审阅详情" direction="rtl">
      <template v-if="previewActivity">
        <h2 style="margin:0 0 12px;color:#133b2a">{{ previewActivity.title }}</h2>
        <div class="preview-meta">
          <div class="field"><span class="field-label">分类</span><span class="field-value">{{ previewActivity.activity_type || '未分类' }}</span></div>
          <div class="field"><span class="field-label">主办方</span><span class="field-value">{{ previewActivity.organizer || '未知' }}</span></div>
          <div class="field"><span class="field-label">时间</span><span class="field-value">{{ previewActivity.event_time ? new Date(previewActivity.event_time).toLocaleString('zh-CN') : '待定' }}</span></div>
          <div class="field"><span class="field-label">地点</span><span class="field-value">{{ previewActivity.location || '待定' }}</span></div>
        </div>
        <div v-if="(previewActivity as any).quality_score != null" class="preview-meta" style="grid-template-columns:1fr">
          <div class="field"><span class="field-label">质量评分</span><span class="field-value">{{ (previewActivity as any).quality_score }}</span></div>
        </div>
        <section class="preview-section" v-if="(previewActivity as any).summary">
          <h3>摘要</h3>
          <div class="preview-body">{{ (previewActivity as any).summary }}</div>
        </section>
        <section class="preview-section" v-if="(previewActivity as any).raw_text">
          <h3>活动正文</h3>
          <div class="preview-body">{{ (previewActivity as any).raw_text }}</div>
        </section>
        <section class="preview-section" v-if="(previewActivity as any).content_html">
          <h3>海报预览</h3>
          <div class="preview-body" v-html="sanitizeHtml((previewActivity as any).content_html)" />
        </section>
        <section class="preview-section" v-if="(previewActivity as any).source_url">
          <h3>来源链接</h3>
          <a :href="(previewActivity as any).source_url" target="_blank" rel="noopener noreferrer" style="color:var(--brand-accent)">{{ (previewActivity as any).source_url }}</a>
        </section>
        <div class="preview-drawer-footer">
          <el-button @click="previewDrawer = false">关闭</el-button>
          <el-button type="danger" @click="review(previewActivity.id, 'reject'); previewDrawer = false">驳回</el-button>
          <el-button type="success" @click="review(previewActivity.id, 'approve'); previewDrawer = false">批准</el-button>
        </div>
      </template>
    </el-drawer>
  </AppShell>
</template>

<style scoped>
.table-wrap { overflow: auto; }
.base-title { color: var(--brand-dark); font-weight: 700; }
.duplicate-item { display: flex; justify-content: space-between; gap: 16px; align-items: center; border-top: 1px solid var(--line); padding: 12px 0; }
.duplicate-item div { display: grid; gap: 4px; }
.duplicate-item span { color: var(--text-muted); font-size: 13px; }

.preview-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 18px; margin-bottom: 18px }
.preview-meta .field { display: grid; gap: 3px }
.preview-meta .field-label { font-size: 12px; color: #889e93 }
.preview-meta .field-value { font-size: 15px; font-weight: 600; color: #1a2e25 }
.preview-section { margin-bottom: 18px }
.preview-section h3 { margin: 0 0 8px; font-size: 15px; color: var(--brand-dark) }
.preview-body { max-height: 50vh; overflow-y: auto; padding: 14px; background: #f7fbf8; border-radius: 10px; white-space: pre-wrap; font-size: 14px; line-height: 1.8; color: #37423e }
.preview-drawer-footer { display: flex; gap: 10px; justify-content: flex-end }
</style>
