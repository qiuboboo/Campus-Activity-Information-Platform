<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import { bulkReviewActivities, getPosterDuplicates, getReviewActivities, mergePosterSource, rebuildPosterKnowledge, reviewActivity } from '@/api/admin'
import { enrichPosterWithAi } from '@/api/ai'
import type { Activity } from '@/api/activities'

const loading = ref(false)
const error = ref('')
const activities = ref<Activity[]>([])
const selected = ref<Activity[]>([])
const duplicateDialog = ref(false)
const duplicateBase = ref<Activity | null>(null)
const duplicates = ref<Activity[]>([])

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
          <el-table-column label="操作" width="330">
            <template #default="{ row }">
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
  </AppShell>
</template>

<style scoped>
.table-wrap { overflow: auto; }
.base-title { color: var(--brand-dark); font-weight: 700; }
.duplicate-item { display: flex; justify-content: space-between; gap: 16px; align-items: center; border-top: 1px solid var(--line); padding: 12px 0; }
.duplicate-item div { display: grid; gap: 4px; }
.duplicate-item span { color: var(--text-muted); font-size: 13px; }
</style>
