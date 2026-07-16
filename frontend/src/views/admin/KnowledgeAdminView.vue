<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import KnowledgeEgoGraph from '@/components/KnowledgeEgoGraph.vue'
import { exportKnowledge } from '@/api/admin'
import { getKnowledgeNode, listKnowledgeNodes, rebuildKnowledge, type KnowledgeNode, type RelatedActivity } from '@/api/knowledge'
import { relationLabel, matchedByLabel } from '@/utils/knowledgeLabels'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const nodes = ref<KnowledgeNode[]>([])
const q = ref('')
const nodeType = ref('')
const drawer = ref(false)
const activeNode = ref<(KnowledgeNode & { posters?: Array<{ relation_type: string; matched_by: string; poster: RelatedActivity }> }) | null>(null)
const rebuildForm = reactive({ status: 'published', source_type: '', rebuild_embeddings: false })
const rebuilding = ref(false)
const graphGroups = computed(() => {
  const groups = new Map<string, KnowledgeNode[]>()
  nodes.value.forEach((node) => {
    const key = node.node_type || 'other'
    groups.set(key, [...(groups.get(key) || []), node])
  })
  return [...groups.entries()].map(([type, items]) => ({ type, items }))
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    nodes.value = (await listKnowledgeNodes({ q: q.value || undefined, node_type: nodeType.value || undefined })).data.items
  } catch (e: any) {
    error.value = e?.response?.data?.message || '知识节点加载失败'
  } finally {
    loading.value = false
  }
}

async function openNode(node: KnowledgeNode) {
  const { data } = await getKnowledgeNode(node.id)
  activeNode.value = data.item
  drawer.value = true
}

const egoRelated = computed(() =>
  (activeNode.value?.posters || []).map((item) => ({
    id: item.poster.id,
    title: item.poster.title,
    relation: item.relation_type,
  })),
)

function openActivity(id: number) {
  drawer.value = false
  router.push(`/activity/${id}`)
}

async function rebuildAll() {
  try {
    await ElMessageBox.confirm('确认按当前条件重建知识图谱吗？', '重建知识图谱', { type: 'warning' })
    rebuilding.value = true
    const { data } = await rebuildKnowledge({
      status: rebuildForm.status || undefined,
      source_type: rebuildForm.source_type || undefined,
      rebuild_embeddings: rebuildForm.rebuild_embeddings,
    })
    ElMessage.success(`重建完成：成功 ${data.succeeded}/${data.total}，失败 ${data.failed}`)
    load()
  } catch {
  } finally {
    rebuilding.value = false
  }
}

async function download() {
  const response = await exportKnowledge()
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = 'knowledge.json'
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<template>
  <AppShell title="知识图谱">
    <template #heading>
      <el-button @click="download">导出知识</el-button>
      <el-button type="primary" :loading="rebuilding" @click="rebuildAll">重建知识</el-button>
    </template>

    <section class="toolbar surface-card">
      <el-input v-model="q" clearable placeholder="搜索节点" @keyup.enter="load" />
      <el-select v-model="nodeType" clearable placeholder="全部类型" @change="load">
        <el-option label="地点" value="place" />
        <el-option label="组织" value="organization" />
        <el-option label="主题" value="topic" />
        <el-option label="时间" value="time" />
        <el-option label="来源" value="source" />
      </el-select>
      <el-button type="primary" @click="load">筛选</el-button>
    </section>

    <section class="surface-card rebuild-box">
      <el-form :inline="true" :model="rebuildForm">
        <el-form-item label="状态">
          <el-select v-model="rebuildForm.status" clearable>
            <el-option label="已发布" value="published" />
            <el-option label="草稿" value="draft" />
            <el-option label="待审核" value="pending_review" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源类型">
          <el-input v-model="rebuildForm.source_type" clearable placeholder="manual / crawl，可留空" />
        </el-form-item>
        <el-form-item label="重建向量">
          <el-switch v-model="rebuildForm.rebuild_embeddings" />
        </el-form-item>
      </el-form>
    </section>

    <section v-if="graphGroups.length" class="surface-card graph-panel">
      <div class="graph-center">
        <strong>知识图谱</strong>
        <span>{{ nodes.length }} 个节点</span>
      </div>
      <button
        v-for="group in graphGroups"
        :key="group.type"
        type="button"
        class="graph-group"
        :class="{ active: nodeType === group.type }"
        @click="nodeType = nodeType === group.type ? '' : group.type; load()"
      >
        <strong>{{ group.type }}</strong>
        <span>{{ group.items.length }} 个节点</span>
        <small>{{ group.items.slice(0, 3).map(item => item.name).join(' / ') }}</small>
      </button>
      <div v-if="nodeType" class="filter-tag">
        已筛选：{{ nodeType }}
        <el-button text size="small" type="primary" @click="nodeType = ''; load()">显示全部</el-button>
      </div>
    </section>

    <PageState :loading="loading" :error="error" :empty="!loading && !error && !nodes.length" empty-text="暂无知识节点" @retry="load">
      <section class="surface-card table-wrap">
        <el-table :data="nodes" @row-click="openNode">
          <el-table-column prop="name" label="节点" min-width="180" />
          <el-table-column prop="node_type" label="类型" width="130" />
          <el-table-column prop="alias" label="别名" min-width="180" />
          <el-table-column prop="description" label="描述" min-width="240" />
        </el-table>
      </section>
    </PageState>

    <el-drawer v-model="drawer" size="min(92vw, 560px)" title="节点详情">
      <template v-if="activeNode">
        <h2>{{ activeNode.name }}</h2>
        <p class="muted">{{ activeNode.node_type }} <span v-if="activeNode.alias">· {{ activeNode.alias }}</span></p>
        <p>{{ activeNode.description || '暂无描述' }}</p>
        <h3>关联网络</h3>
        <KnowledgeEgoGraph
          v-if="egoRelated.length"
          :center-name="activeNode.name"
          :center-type="activeNode.node_type"
          :related="egoRelated"
          @open="openActivity"
        />
        <h3>关联活动</h3>
        <el-empty v-if="!activeNode.posters?.length" description="暂无关联活动" />
        <article v-for="item in activeNode.posters" v-else :key="`${item.poster.id}-${item.relation_type}`" class="poster-line">
          <strong>{{ item.poster.title }}</strong>
          <span>{{ relationLabel(item.relation_type) }} · {{ matchedByLabel(item.matched_by) }}</span>
        </article>
      </template>
    </el-drawer>
  </AppShell>
</template>

<style scoped>
.toolbar, .rebuild-box { padding: 14px; margin-bottom: 16px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.toolbar :deep(.el-input) { max-width: 320px; }
.graph-panel { margin-bottom: 16px; padding: 18px; display: grid; grid-template-columns: 180px repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; align-items: stretch; }
.graph-center, .graph-group { border-radius: 8px; padding: 14px; }
.graph-center { display: grid; place-content: center; text-align: center; color: #fff; background: var(--brand); }
.graph-center strong { font-size: 18px; }
.graph-center span { opacity: .9; margin-top: 4px; }
.graph-group { border: 2px solid transparent; background: #f8fbf9; text-align: left; cursor: pointer; color: var(--brand-dark); display: grid; gap: 6px; }
.graph-group:hover { border-color: var(--brand-accent); background: var(--brand-soft); }
.graph-group.active { border-color: var(--brand); background: var(--brand-soft); box-shadow: 0 0 0 1px var(--brand); }
.filter-tag { grid-column: 1 / -1; display: flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 6px; background: #eef6f1; color: var(--brand-dark); font-size: 13px; }
.graph-group span, .graph-group small { color: var(--text-muted); }
.graph-group small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.table-wrap { overflow: auto; }
h2 { margin: 0 0 8px; color: var(--brand-dark); }
h3 { color: var(--brand-dark); margin-top: 22px; }
.muted { color: var(--text-muted); }
.poster-line { padding: 12px 0; border-top: 1px solid var(--line); display: grid; gap: 4px; }
.poster-line span { color: var(--text-muted); font-size: 13px; }
</style>
