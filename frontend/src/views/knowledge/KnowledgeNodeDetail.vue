<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getKnowledgeNode } from '@/api/knowledge'

const route = useRoute()
const router = useRouter()

const node = ref<any>(null)
const posters = ref<any[]>([])
const loading = ref(true)

async function fetchData() {
  try {
    const id = Number(route.params.id)
    const res = await getKnowledgeNode(id)
    node.value = res.data.item
    posters.value = res.data.item.posters || []
  } catch {
    router.push('/knowledge')
  } finally {
    loading.value = false
  }
}

const typeColors: Record<string, string> = {
  time: 'success',
  place: 'primary',
  organization: 'warning',
  topic: 'danger',
  source: 'info',
}

onMounted(fetchData)
</script>

<template>
  <div v-loading="loading">
    <el-button text type="primary" @click="router.push('/knowledge')" style="margin-bottom: 12px;">
      <el-icon><ArrowLeft /></el-icon> 返回知识图谱
    </el-button>

    <el-card v-if="node" shadow="hover" style="border-radius: 8px;">
      <template #header>
        <div style="display: flex; align-items: center; gap: 12px;">
          <span style="font-size: 20px; font-weight: bold; color: #303133;">{{ node.name }}</span>
          <el-tag :type="(typeColors[node.node_type] as any) || 'info'" size="small">
            {{ node.node_type }}
          </el-tag>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="描述">
          {{ node.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="别名">
          {{ node.alias || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="来源链接">
          {{ node.source_url || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <h4 style="margin: 24px 0 12px; color: #303133;">关联海报 ({{ posters.length }})</h4>
      <el-table :data="posters" stripe @row-click="(row: any) => router.push(`/posters/${row.poster?.id}`)" style="cursor: pointer;">
        <el-table-column prop="poster.title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="relation_type" label="关系类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.relation_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/posters/${row.poster?.id}`)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
