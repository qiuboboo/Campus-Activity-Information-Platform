<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import ActivityList from '@/components/ActivityList.vue'
import PageState from '@/components/PageState.vue'
import { searchActivities, type SearchResult } from '@/api/search'
import { sortActivities } from '@/utils/activitySort'

const route = useRoute(); const router = useRouter()
const loading = ref(false); const error = ref(''); const items = ref<SearchResult[]>([]); const total = ref(0)
const q = ref(String(route.query.q || '')); const scope = ref((route.query.scope === 'external' ? 'external' : 'internal') as 'internal' | 'external')
const category = ref(String(route.query.activity_type || '')); const page = ref(Number(route.query.page || 1)); const sort = ref(String(route.query.sort || 'relevance'))
const categories = ['讲座', '晚会', '竞赛', '论坛', '展览', '招聘', '体育', '其他']
const title = computed(() => q.value ? `“${q.value}”的搜索结果` : '活动搜索')

async function load() {
  if (!q.value.trim()) { items.value = []; total.value = 0; return }
  loading.value = true; error.value = ''
  try { const { data } = await searchActivities(scope.value, { q: q.value.trim(), page: page.value, per_page: 10, activity_type: category.value || undefined, sort: sort.value as any }); items.value = sort.value === 'relevance' ? data.items : sortActivities(data.items.map(item => item.item), sort.value as 'created_at' | 'event_time').map(activity => data.items.find(item => item.item.id === activity.id)!).filter(Boolean); total.value = data.total } catch (e: any) { error.value = e?.response?.data?.message || '暂时无法完成搜索' } finally { loading.value = false }
}
async function syncAndLoad(reset = false) {
  if (reset) page.value = 1
  const query = { q: q.value || undefined, scope: scope.value === 'external' ? 'external' : undefined, activity_type: category.value || undefined, sort: sort.value === 'relevance' ? undefined : sort.value, page: page.value > 1 ? String(page.value) : undefined }
  const changed = JSON.stringify(query) !== JSON.stringify(route.query)
  if (changed) await router.replace({ query })
  else await load()
}
watch(() => route.query, () => { q.value = String(route.query.q || ''); scope.value = route.query.scope === 'external' ? 'external' : 'internal'; category.value = String(route.query.activity_type || ''); sort.value = String(route.query.sort || 'relevance'); page.value = Number(route.query.page || 1); load() })
onMounted(load)
</script>

<template><AppShell :title="title"><template #heading><el-button @click="router.push('/activities')">浏览全部活动</el-button></template>
  <section class="search-bar surface-card"><el-input v-model="q" size="large" placeholder="输入活动、地点或主办方" @keyup.enter="syncAndLoad(true)" /><el-button type="primary" size="large" @click="syncAndLoad(true)">搜索</el-button></section>
  <section class="filters surface-card"><el-radio-group v-model="scope" @change="syncAndLoad(true)"><el-radio-button value="internal">校内搜索</el-radio-button><el-radio-button value="external">外部搜索</el-radio-button></el-radio-group><el-select v-model="category" clearable placeholder="全部分类" @change="syncAndLoad(true)"><el-option v-for="item in categories" :key="item" :label="item" :value="item" /></el-select><el-select v-model="sort" @change="syncAndLoad(true)"><el-option label="相关度" value="relevance" /><el-option label="活动时间" value="event_time" /><el-option label="最新发布" value="created_at" /></el-select></section>
  <PageState :loading="loading" :error="error" :empty="!loading && !error && !!q && items.length === 0" empty-text="未找到匹配活动" @retry="load"><ActivityList :activities="items.map(item => item.item)" /><p v-if="scope === 'external' && items.length" class="external-note">外部搜索结果仅供参考，请以来源页面为准。</p><el-pagination v-if="total > 10" v-model:current-page="page" layout="prev, pager, next" :page-size="10" :total="total" @current-change="syncAndLoad()" /></PageState>
</AppShell></template>
<style scoped>.search-bar,.filters{padding:16px;display:flex;gap:12px;margin-bottom:16px}.search-bar :deep(.el-input){flex:1}.filters{align-items:center;flex-wrap:wrap}.external-note{color:var(--text-muted);font-size:13px;margin:14px 0}@media(max-width:600px){.search-bar{flex-direction:column}}</style>
