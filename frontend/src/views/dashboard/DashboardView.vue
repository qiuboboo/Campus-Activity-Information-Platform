<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'
import { listPosters } from '@/api/posters'
import { listKnowledgeNodes } from '@/api/knowledge'

interface Summary {
  posters: { total: number; published: number; draft: number; rejected: number }
  knowledge_nodes: number
  poster_links: number
  data_sources: number
  last_crawl: {
    id: number
    data_source_id: number
    status: string
    pages_found: number
    pages_succeeded: number
    drafts_created: number
    average_quality_score: number | null
    started_at: string
    finished_at: string | null
  } | null
}

const router = useRouter()
const summary = ref<Summary | null>(null)
const recentPosters = ref<any[]>([])
const loading = ref(true)

async function fetchData() {
  try {
    const [summaryRes, postersRes] = await Promise.all([
      client.get<Summary>('/demo/summary'),
      listPosters({ per_page: 5 }),
    ])
    summary.value = summaryRes.data
    recentPosters.value = postersRes.data.items
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(fetchData)
</script>

<template>
  <div class="dashboard">
    <h2 style="margin-bottom: 20px; color: #303133;">数据看板</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card" @click="router.push('/posters')" style="cursor: pointer;">
          <div class="stat-inner">
            <div class="stat-icon" style="background: #ecf5ff; color: #409eff;">
              <el-icon size="24"><Document /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ summary?.posters.total ?? '-' }}</div>
              <div class="stat-label">总海报数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon" style="background: #f0f9eb; color: #67c23a;">
              <el-icon size="24"><SuccessFilled /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ summary?.posters.published ?? '-' }}</div>
              <div class="stat-label">已发布</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon" style="background: #fef0f0; color: #f56c6c;">
              <el-icon size="24"><WarningFilled /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ summary?.posters.draft ?? '-' }}</div>
              <div class="stat-label">待处理</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c;">
              <el-icon size="24"><Connection /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ summary?.knowledge_nodes ?? '-' }}</div>
              <div class="stat-label">知识节点</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行统计 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon" style="background: #f0f9eb; color: #67c23a;">
              <el-icon size="24"><Share /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ summary?.poster_links ?? '-' }}</div>
              <div class="stat-label">海报关联</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon" style="background: #ecf5ff; color: #409eff;">
              <el-icon size="24"><Setting /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ summary?.data_sources ?? '-' }}</div>
              <div class="stat-label">数据源</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c;">
              <el-icon size="24"><Timer /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ summary?.last_crawl ? formatTime(summary.last_crawl.started_at) : '-' }}</div>
              <div class="stat-label">最近抓取</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon" style="background: #fef0f0; color: #f56c6c;">
              <el-icon size="24"><TrendCharts /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ summary?.last_crawl?.average_quality_score ?? '-' }}</div>
              <div class="stat-label">平均质量分</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-card shadow="hover" class="recent-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: bold; color: #303133;">最新活动</span>
          <el-button text type="primary" @click="router.push('/posters')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentPosters" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="event_time" label="活动时间" width="160">
          <template #default="{ row }">
            {{ row.event_time ? formatTime(row.event_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="140" show-overflow-tooltip />
        <el-table-column prop="organizer" label="主办方" width="130" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'published' ? 'success' :
                row.status === 'draft' ? 'info' :
                row.status === 'pending_review' ? 'warning' : 'danger'
              "
              size="small"
            >
              {{
                row.status === 'published' ? '已发布' :
                row.status === 'draft' ? '草稿' :
                row.status === 'pending_review' ? '待审核' : '已拒绝'
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/posters/${row.id}`)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
}
.stat-row {
  margin-bottom: 16px;
}
.stat-card {
  margin-bottom: 0;
  border-radius: 8px;
  transition: transform 0.2s;
}
.stat-card:hover {
  transform: translateY(-2px);
}
.stat-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.recent-card {
  margin-top: 4px;
  border-radius: 8px;
}
</style>
