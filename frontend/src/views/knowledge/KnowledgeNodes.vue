<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listKnowledgeNodes, type KnowledgeNode } from '@/api/knowledge'

const router = useRouter()

const nodes = ref<KnowledgeNode[]>([])
const keyword = ref('')
const typeFilter = ref('')
const loading = ref(false)

const nodeTypeOptions = [
  { value: '', label: '全部' },
  { value: 'time', label: '时间' },
  { value: 'place', label: '地点' },
  { value: 'organization', label: '组织' },
  { value: 'topic', label: '主题' },
  { value: 'source', label: '来源' },
]

const typeColors: Record<string, string> = {
  time: 'success',
  place: 'primary',
  organization: 'warning',
  topic: 'danger',
  source: 'info',
}

async function fetchData() {
  loading.value = true
  try {
    const res = await listKnowledgeNodes({
      q: keyword.value || undefined,
      node_type: typeFilter.value || undefined,
    })
    nodes.value = res.data.items
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  fetchData()
}

onMounted(fetchData)
</script>

<template>
  <div>
    <h2 style="margin-bottom: 16px; color: #303133;">知识图谱</h2>

    <el-card shadow="hover" style="border-radius: 8px;">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input v-model="keyword" placeholder="节点名称/描述" clearable style="width: 200px;" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="typeFilter" style="width: 120px" clearable>
            <el-option v-for="opt in nodeTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :icon="'Search'">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="nodes" v-loading="loading" stripe @row-click="(row: KnowledgeNode) => router.push(`/knowledge/${row.id}`)" style="cursor: pointer;">
        <el-table-column prop="name" label="节点名称" min-width="200" />
        <el-table-column prop="node_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="(typeColors[row.node_type] as any) || 'info'" size="small">
              {{ nodeTypeOptions.find(o => o.value === row.node_type)?.label || row.node_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="alias" label="别名" width="180" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
