<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import ActivityList from '@/components/ActivityList.vue'
import PageState from '@/components/PageState.vue'
import { listActivities, type Activity } from '@/api/activities'
import { sortActivities, type ActivitySort } from '@/utils/activitySort'

const route = useRoute(); const router = useRouter(); const loading = ref(false); const error = ref(''); const activities = ref<Activity[]>([]); const total = ref(0)
const q = ref(String(route.query.q || '')); const category = ref(String(route.query.activity_type || '')); const sort = ref((route.query.sort === 'event_time' ? 'event_time' : 'created_at') as ActivitySort); const page = ref(Number(route.query.page || 1)); const categories = ['讲座','晚会','竞赛','论坛','展览','招聘','体育','其他']
async function load(){loading.value=true;error.value='';try{const {data}=await listActivities({q:q.value||undefined,activity_type:category.value||undefined,sort:sort.value,page:page.value,per_page:10});activities.value=sortActivities(data.items,sort.value);total.value=data.total}catch(e:any){error.value=e?.response?.data?.message||'活动列表加载失败'}finally{loading.value=false}}
async function apply(reset=false){if(reset)page.value=1;const query={q:q.value||undefined,activity_type:category.value||undefined,sort:sort.value==='event_time'?'event_time':undefined,page:page.value>1?String(page.value):undefined};if(JSON.stringify(query)===JSON.stringify(route.query))await load();else await router.replace({query})}
watch(() => route.query, () => {q.value=String(route.query.q||'');category.value=String(route.query.activity_type||'');sort.value=route.query.sort==='event_time'?'event_time':'created_at';page.value=Number(route.query.page||1);load()},{immediate:true})
</script>
<template><AppShell title="全部活动"><template #heading><el-button type="primary" @click="router.push('/search')">高级搜索</el-button></template><section class="toolbar surface-card"><el-input v-model="q" placeholder="搜索活动" clearable @keyup.enter="apply(true)"/><el-select v-model="category" clearable placeholder="全部分类" @change="apply(true)"><el-option v-for="item in categories" :key="item" :label="item" :value="item"/></el-select><el-select v-model="sort" aria-label="活动排序" @change="apply(true)"><el-option label="最新发布" value="created_at"/><el-option label="最近活动时间" value="event_time"/></el-select><el-button type="primary" @click="apply(true)">筛选</el-button></section><PageState :loading="loading" :error="error" :empty="!loading&&!error&&!activities.length" empty-text="暂无活动" @retry="load"><ActivityList :activities="activities"/><el-pagination v-if="total>10" v-model:current-page="page" :total="total" :page-size="10" layout="prev, pager, next" @current-change="apply()"/></PageState></AppShell></template>
<style scoped>.toolbar{display:flex;gap:12px;padding:16px;margin-bottom:16px}.toolbar :deep(.el-input){max-width:420px}@media(max-width:600px){.toolbar{flex-wrap:wrap}.toolbar :deep(.el-input){max-width:none;flex-basis:100%}}</style>
