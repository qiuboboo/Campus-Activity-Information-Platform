<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import { listMyActivities, submitActivityForReview, type Activity } from '@/api/activities'
import { ElMessage, ElMessageBox } from 'element-plus'

const router=useRouter();const loading=ref(false);const error=ref('');const activities=ref<Activity[]>([]);const status=ref('');const q=ref('');const page=ref(1);const total=ref(0)
async function load(){loading.value=true;error.value='';try{const {data}=await listMyActivities({status:status.value||undefined,q:q.value||undefined,page:page.value,per_page:10});activities.value=data.items;total.value=data.total}catch(e:any){error.value=e?.response?.data?.message||'活动管理列表加载失败'}finally{loading.value=false}}
function filter(){page.value=1;load()}
async function submit(id:number){try{await ElMessageBox.confirm('提交后将进入审核队列，确认继续？','提交审核',{type:'warning'});await submitActivityForReview(id);ElMessage.success('已提交审核');load()}catch{}}
onMounted(load)
</script>
<template>
  <AppShell title="我的发布">
    <template #heading><el-button type="primary" @click="router.push('/activities/create')">创建活动</el-button></template>
    <section class="toolbar surface-card"><el-input v-model="q" placeholder="搜索我的活动" @keyup.enter="filter"/><el-select v-model="status" clearable placeholder="全部状态" @change="filter"><el-option label="草稿" value="draft"/><el-option label="待审核" value="pending_review"/><el-option label="已发布" value="published"/><el-option label="已驳回" value="rejected"/></el-select><el-button type="primary" @click="filter">筛选</el-button></section>
    <PageState :loading="loading" :error="error" :empty="!loading&&!error&&!activities.length" empty-text="还没有创建活动" @retry="load">
      <section class="surface-card table-wrap">
        <el-table :data="activities">
          <el-table-column prop="title" label="活动" min-width="180"/><el-table-column prop="activity_type" label="分类" width="100"/>
          <el-table-column label="状态" width="120"><template #default="{ row }"><el-tag :type="row.status==='published'?'success':row.status==='rejected'?'danger':'warning'">{{ row.status }}</el-tag></template></el-table-column>
          <el-table-column label="审核反馈" min-width="180"><template #default="{ row }"><span v-if="row.status==='rejected'">{{ row.reject_reason || '请联系管理员了解驳回原因' }}</span><span v-else>—</span></template></el-table-column>
          <el-table-column prop="event_time" label="活动时间" min-width="160"/>
          <el-table-column label="操作" width="190"><template #default="{ row }"><el-button text type="primary" @click="router.push(`/activity/${row.id}`)">查看</el-button><el-button v-if="row.status==='draft'||row.status==='rejected'" text type="primary" @click="router.push(`/activities/${row.id}/edit`)">编辑</el-button><el-button v-if="row.status==='draft'||row.status==='rejected'" text type="success" @click="submit(row.id)">提交审核</el-button></template></el-table-column>
        </el-table>
      </section>
      <el-pagination v-if="total>10" v-model:current-page="page" :total="total" :page-size="10" layout="prev, pager, next" @current-change="load"/>
    </PageState>
  </AppShell>
</template>
<style scoped>.toolbar{display:flex;gap:12px;padding:16px;margin-bottom:16px}.toolbar :deep(.el-input){max-width:360px}.table-wrap{overflow:auto}@media(max-width:600px){.toolbar{flex-wrap:wrap}.toolbar :deep(.el-input){max-width:none;flex-basis:100%}}</style>
