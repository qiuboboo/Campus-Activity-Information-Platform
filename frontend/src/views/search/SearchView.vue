<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { internalSearch as apiInternalSearch, externalSearch as apiExternalSearch } from '@/api/search'

const router = useRouter()

const keyword = ref('')
const results = ref<any[]>([])
const loading = ref(false)
const searched = ref(false)
const searchMode = ref('')
const activeTab = ref('internal')

const statusTagMap: Record<string, string> = {
  draft: 'info',
  pending_review: 'warning',
  published: 'success',
  rejected: 'danger',
}

async function doSearch() {
  if (!keyword.value.trim()) return
  loading.value = true
  searched.value = true
  try {
    if (activeTab.value === 'internal') {
      const res = await apiInternalSearch(keyword.value)
      results.value = res.data.items
      searchMode.value = res.data.search_mode
    } else {
      const res = await apiExternalSearch(keyword.value)
      results.value = (res.data.results || []).map((r: any) => ({ hit_type: 'external', item: r }))
      searchMode.value = 'external'
    }
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <div>
    <h2 style="margin-bottom: 16px; color: #303133;">搜索</h2>

    <el-card shadow="hover" style="border-radius: 8px;">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="内部搜索" name="internal" />
        <el-tab-pane label="外部搜索" name="external" />
      </el-tabs>

      <el-form :inline="true" @submit.prevent="doSearch">
        <el-form-item style="width: 400px;">
          <el-input
            v-model="keyword"
            placeholder="输入关键词搜索活动、知识节点..."
            clearable
            size="large"
            @keyup.enter="doSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="doSearch" size="large">搜索</el-button>
        </el-form-item>
      </el-form>

      <div v-if="searched && !loading">
        <div style="color: #909399; margin-bottom: 12px; font-size: 13px;">
          搜索模式: {{ searchMode === 'vector' ? '语义向量' : '全文检索' }}
          | 共 {{ results.length }} 条结果
        </div>

        <div v-if="results.length === 0" style="text-align: center; padding: 40px; color: #909399;">
          未找到相关内容
        </div>

        <div v-for="(hit, idx) in results" :key="idx" style="margin-bottom: 12px;">
          <!-- 海报命中 -->
          <el-card v-if="hit.hit_type === 'poster'" shadow="hover" @click="router.push(`/posters/${hit.item.id}`)" style="cursor: pointer; border-radius: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <div>
                <div style="font-weight: bold; color: #303133; margin-bottom: 4px;">
                  {{ hit.item.title }}
                  <el-tag :type="(statusTagMap[hit.item.status] as any) || 'info'" size="small" style="margin-left: 8px;">
                    {{ hit.item.status }}
                  </el-tag>
                </div>
                <div style="font-size: 13px; color: #909399;">
                  {{ hit.item.summary?.substring(0, 120) }}
                </div>
                <div style="font-size: 12px; color: #c0c4cc; margin-top: 4px;">
                  {{ hit.item.location || '-' }} | {{ formatTime(hit.item.event_time) }} | {{ hit.item.organizer || '-' }}
                </div>
              </div>
              <el-tag size="small" type="primary" effect="plain">海报</el-tag>
            </div>
          </el-card>

          <!-- 知识节点命中 -->
          <el-card v-else-if="hit.hit_type === 'knowledge_node'" shadow="hover" @click="router.push(`/knowledge/${hit.item.id}`)" style="cursor: pointer; border-radius: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <div>
                <div style="font-weight: bold; color: #303133; margin-bottom: 4px;">
                  {{ hit.item.name }}
                </div>
                <div style="font-size: 13px; color: #909399;">
                  {{ hit.item.description || '-' }}
                </div>
              </div>
              <el-tag size="small" type="warning" effect="plain">知识节点</el-tag>
            </div>
          </el-card>

          <!-- 外部搜索结果 -->
          <el-card v-else shadow="hover" style="border-radius: 6px;">
            <div>
              <div style="font-weight: bold; color: #303133; margin-bottom: 4px;">
                {{ hit.item.title || hit.item.name || '外部结果' }}
              </div>
              <div style="font-size: 13px; color: #909399;">
                {{ hit.item.content || hit.item.description || hit.item.snippet || '-' }}
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>
</template>
