<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import { getAdminSummary, type AdminSummary } from '@/api/admin'

const router = useRouter()
const summary = ref<AdminSummary>()
const loading = ref(false)
const error = ref('')

// 状态语义色,经 dataviz 六项校验 (光模式面 #fcfcfb 下全部通过)
const STATUS_META = [
  { key: 'published', label: '已发布', color: '#0e7d4c' },
  { key: 'pending', label: '待审核', color: '#b5830f' },
  { key: 'draft', label: '草稿', color: '#3d78b3' },
  { key: 'rejected', label: '已驳回', color: '#a63a34' },
] as const

const statusRows = computed(() => {
  const posters = summary.value?.posters
  if (!posters) return []
  const counts: Record<string, number> = {
    published: posters.published,
    pending: summary.value?.pending ?? 0,
    draft: posters.draft,
    rejected: posters.rejected,
  }
  const max = Math.max(1, ...Object.values(counts))
  return STATUS_META.map((meta) => ({
    ...meta,
    count: counts[meta.key],
    pct: Math.round((counts[meta.key] / max) * 100),
  }))
})

const lastCrawl = computed(() => summary.value?.last_crawl ?? null)
const crawlPagesTotal = computed(() => {
  const crawl = lastCrawl.value
  if (!crawl) return 0
  return Math.max(1, crawl.pages_succeeded + crawl.pages_failed)
})
const formatTime = (value?: string | null) =>
  value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-'

const tools = [
  { title: '审核队列', desc: '处理发布者提交和爬虫草稿', path: '/admin/review' },
  { title: '数据源', desc: '维护爬取来源、查看日志和任务状态', path: '/admin/data-sources' },
  { title: '知识图谱', desc: '查看节点、关联活动并重建知识', path: '/admin/knowledge' },
  { title: 'AI 配置', desc: '查看当前 LLM、搜索和 Embedding 配置', path: '/admin/ai-config' },
  { title: '字典管理', desc: '维护地点、组织和主题标准词', path: '/admin/dicts' },
  { title: '审计日志', desc: '追踪关键后台操作并导出数据', path: '/admin/audit-logs' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    summary.value = (await getAdminSummary()).data
  } catch (e: any) {
    error.value = e?.response?.data?.message || '看板加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <AppShell title="管理看板">
    <PageState :loading="loading" :error="error" @retry="load">
      <div v-if="summary" class="stats">
        <article class="surface-card">
          <strong>{{ summary.pending }}</strong>
          <span>待审核活动</span>
          <el-button text type="primary" @click="router.push('/admin/review')">前往审核</el-button>
        </article>
        <article class="surface-card">
          <strong>{{ summary.published }}</strong>
          <span>已发布活动</span>
          <el-button text type="primary" @click="router.push('/activities')">浏览活动</el-button>
        </article>
        <article class="surface-card">
          <strong>{{ summary.sources }}</strong>
          <span>数据源</span>
          <el-button text type="primary" @click="router.push('/admin/data-sources')">管理数据源</el-button>
        </article>
        <article class="surface-card">
          <strong>{{ summary.failed_tasks }}</strong>
          <span>异常任务</span>
          <el-button text type="primary" @click="router.push('/admin/audit-logs')">查看审计</el-button>
        </article>
      </div>

      <div v-if="summary" class="insight-grid">
        <section class="surface-card panel">
          <h2>活动状态分布</h2>
          <div class="status-chart" role="img" aria-label="各状态活动数量分布">
            <div v-for="row in statusRows" :key="row.key" class="status-row" :title="`${row.label} ${row.count} 个`">
              <span class="status-label"><i class="status-chip" :style="{ background: row.color }" />{{ row.label }}</span>
              <span class="status-bar-track">
                <span class="status-bar-fill" :style="{ width: `${row.pct}%`, background: row.color }" />
              </span>
              <span class="status-value">{{ row.count }}</span>
            </div>
          </div>
          <div class="coverage-strip">
            <strong>{{ summary.posters?.total ?? '-' }}<span>活动总数</span></strong>
            <strong>{{ summary.knowledge_nodes ?? '-' }}<span>知识节点</span></strong>
            <strong>{{ summary.poster_links ?? '-' }}<span>关联边</span></strong>
          </div>
        </section>

        <section class="surface-card panel crawl-panel">
          <h2>最近一次爬取</h2>
          <template v-if="lastCrawl">
            <div class="crawl-head">
              <el-tag :type="lastCrawl.status === 'success' ? 'success' : 'danger'" effect="plain">
                {{ lastCrawl.status === 'success' ? '成功' : '失败' }}
              </el-tag>
              <span class="crawl-time">{{ formatTime(lastCrawl.started_at) }} 开始</span>
            </div>
            <div class="crawl-pages" :title="`成功 ${lastCrawl.pages_succeeded} 页 / 失败 ${lastCrawl.pages_failed} 页`">
              <span class="pages-label">页面 {{ lastCrawl.pages_found }}</span>
              <span class="pages-track">
                <span class="pages-seg pages-ok" :style="{ width: `${(lastCrawl.pages_succeeded / crawlPagesTotal) * 100}%` }" />
                <span v-if="lastCrawl.pages_failed" class="pages-seg pages-bad" :style="{ width: `${(lastCrawl.pages_failed / crawlPagesTotal) * 100}%` }" />
              </span>
              <span class="pages-value">{{ lastCrawl.pages_succeeded }} 成功<template v-if="lastCrawl.pages_failed"> · {{ lastCrawl.pages_failed }} 失败</template></span>
            </div>
            <div class="crawl-facts">
              <strong>{{ lastCrawl.drafts_created }}<span>新建草稿</span></strong>
              <strong>{{ lastCrawl.duplicates_skipped }}<span>去重跳过</span></strong>
              <strong>{{ lastCrawl.average_quality_score ?? '-' }}<span>平均质量分</span></strong>
            </div>
          </template>
          <el-empty v-else description="还没有爬取记录" :image-size="72">
            <el-button type="primary" @click="router.push('/admin/data-sources')">去数据源触发一次爬取</el-button>
          </el-empty>
        </section>
      </div>

      <section class="tool-grid">
        <button v-for="tool in tools" :key="tool.path" class="surface-card tool-card" type="button" @click="router.push(tool.path)">
          <strong>{{ tool.title }}</strong>
          <span>{{ tool.desc }}</span>
        </button>
      </section>
    </PageState>
  </AppShell>
</template>

<style scoped>
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.stats article { padding: 22px; display: grid; gap: 8px; }
.stats strong { color: var(--brand); font-size: 32px; }
.stats span { color: var(--text-muted); }

.insight-grid { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 16px; margin-top: 18px; }
.panel { padding: 22px; }
.panel h2 { margin: 0 0 16px; color: var(--brand-dark); font-size: 17px; }

/* 状态分布: 横向细条,直接标值,色样在标签侧 */
.status-chart { display: grid; gap: 10px; }
.status-row { display: grid; grid-template-columns: 88px minmax(0, 1fr) 40px; gap: 10px; align-items: center; border-radius: 6px; padding: 2px 4px; }
.status-row:hover { background: #f5f8f6; }
.status-label { display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted); font-size: 13px; }
.status-chip { width: 10px; height: 10px; border-radius: 3px; flex: 0 0 10px; }
.status-bar-track { display: block; height: 12px; border-radius: 4px; background: #eef2ef; overflow: hidden; }
.status-bar-fill { display: block; height: 100%; border-radius: 0 4px 4px 0; min-width: 2px; }
.status-value { color: var(--text-main); font-size: 13px; font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; }

.coverage-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 16px; }
.coverage-strip strong { padding: 12px; border-radius: 8px; background: #f7fbf8; color: var(--brand-dark); font-size: 20px; }
.coverage-strip span { display: block; margin-top: 4px; color: var(--text-muted); font-size: 12px; font-weight: 500; }

.crawl-head { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.crawl-time { color: var(--text-muted); font-size: 13px; }
.crawl-pages { display: grid; grid-template-columns: 70px minmax(0, 1fr); gap: 6px 10px; align-items: center; }
.pages-label { color: var(--text-muted); font-size: 13px; }
.pages-track { display: flex; gap: 2px; height: 12px; border-radius: 4px; background: #eef2ef; overflow: hidden; }
.pages-seg { display: block; height: 100%; min-width: 2px; }
.pages-ok { background: #0e7d4c; }
.pages-bad { background: #a63a34; }
.pages-value { grid-column: 2; color: var(--text-muted); font-size: 12px; }
.crawl-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 16px; }
.crawl-facts strong { padding: 12px; border-radius: 8px; background: #f7fbf8; color: var(--brand-dark); font-size: 20px; }
.crawl-facts span { display: block; margin-top: 4px; color: var(--text-muted); font-size: 12px; font-weight: 500; }

.tool-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 20px; }
.tool-card { padding: 20px; text-align: left; cursor: pointer; background: #fff; }
.tool-card:hover { border-color: var(--brand-accent); background: #f8fbf9; }
.tool-card strong { display: block; color: var(--brand-dark); font-size: 17px; margin-bottom: 6px; }
.tool-card span { color: var(--text-muted); line-height: 1.6; }
@media (max-width: 900px) { .stats, .tool-grid { grid-template-columns: repeat(2, 1fr); } .insight-grid { grid-template-columns: 1fr; } }
@media (max-width: 520px) { .stats, .tool-grid { grid-template-columns: 1fr; } }
</style>
