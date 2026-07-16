<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import PageState from '@/components/PageState.vue'
import { createDictEntry, deleteDictEntry, getDictSuggestions, listDictEntries, seedDictEntries, updateDictEntry, type DictCategory, type DictEntry } from '@/api/dicts'

const category = ref<DictCategory>('place')
const q = ref('')
const loading = ref(false)
const error = ref('')
const entries = ref<DictEntry[]>([])
const total = ref(0)
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ standard_name: '', aliases: '', description: '' })

const labels: Record<DictCategory, string> = { place: '地点', org: '组织', topic: '主题' }

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listDictEntries(category.value, { q: q.value || undefined, per_page: 100 })
    entries.value = data.items
    total.value = data.total
  } catch (e: any) {
    error.value = e?.response?.data?.message || '字典加载失败'
  } finally {
    loading.value = false
  }
}

function open(entry?: DictEntry) {
  editingId.value = entry?.id || null
  Object.assign(form, entry ? {
    standard_name: entry.standard_name,
    aliases: entry.aliases || '',
    description: entry.description || '',
  } : { standard_name: '', aliases: '', description: '' })
  dialog.value = true
}

async function save() {
  if (!form.standard_name.trim()) return ElMessage.warning('请输入标准名称')
  const data = {
    standard_name: form.standard_name.trim(),
    aliases: form.aliases.trim(),
    description: form.description.trim(),
  }
  if (editingId.value) await updateDictEntry(category.value, editingId.value, data)
  else await createDictEntry(category.value, data)
  dialog.value = false
  ElMessage.success('字典项已保存')
  load()
}

async function remove(entry: DictEntry) {
  try {
    await ElMessageBox.confirm(`确认删除“${entry.standard_name}”？`, '删除字典项', { type: 'warning' })
    await deleteDictEntry(category.value, entry.id)
    ElMessage.success('已删除')
    load()
  } catch {}
}

const suggestDialog = ref(false)
const suggestions = ref<Array<{ value: string; count: number }>>([])
const suggestLoading = ref(false)
const checked = ref<string[]>([])
async function loadSuggestions() {
  suggestLoading.value = true
  try { const { data } = await getDictSuggestions(category.value); suggestions.value = data.items } catch { ElMessage.error('获取建议失败') } finally { suggestLoading.value = false }
  suggestDialog.value = true
}
async function addSuggestions(selected: string[]) {
  for (const value of selected) { try { await createDictEntry(category.value as DictCategory, { standard_name: value, aliases: '', description: '' }) } catch {} }
  ElMessage.success(`已添加 ${selected.length} 个条目`)
  suggestDialog.value = false
  load()
}

async function seed() {
  const { data } = await seedDictEntries()
  ElMessage.success(data.seeded ? `已导入 ${data.seeded} 条内置别名` : '内置别名已存在')
  load()
}

onMounted(load)
</script>

<template>
  <AppShell title="字典管理">
    <template #heading>
      <el-button @click="seed">导入内置别名</el-button>
      <el-button @click="loadSuggestions">从活动提取</el-button>
      <el-button type="primary" @click="open()">新增字典项</el-button>
    </template>

    <section class="toolbar surface-card">
      <el-segmented v-model="category" :options="Object.entries(labels).map(([value, label]) => ({ value, label }))" @change="load" />
      <el-input v-model="q" clearable placeholder="搜索标准名称或描述" @keyup.enter="load" />
      <el-button type="primary" @click="load">搜索</el-button>
      <span>共 {{ total }} 条</span>
    </section>

    <PageState :loading="loading" :error="error" :empty="!loading && !error && !entries.length" empty-text="暂无字典项" @retry="load">
      <section class="surface-card table-wrap">
        <el-table :data="entries">
          <el-table-column prop="standard_name" label="标准名称" min-width="160" />
          <el-table-column prop="aliases" label="别名" min-width="220" />
          <el-table-column prop="description" label="描述" min-width="240" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button text type="primary" @click="open(row)">编辑</el-button>
              <el-button text type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </PageState>

    <el-dialog v-model="dialog" :title="editingId ? '编辑字典项' : '新增字典项'" width="min(92vw, 520px)">
      <el-form label-position="top">
        <el-form-item label="标准名称"><el-input v-model="form.standard_name" /></el-form-item>
        <el-form-item label="别名"><el-input v-model="form.aliases" placeholder="多个别名用英文逗号分隔" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="suggestDialog" title="从活动提取词条" width="min(92vw, 560px)">
      <p v-if="!suggestions.length && !suggestLoading" style="color:var(--text-muted)">没有可提取的值，所有出现的词条已收录。</p>
      <el-table :data="suggestions" v-loading="suggestLoading" @selection-change="checked = ($event as Array<{value:string}>).map(r => r.value)">
        <el-table-column type="selection" width="48" />
        <el-table-column prop="value" label="值" min-width="160" />
        <el-table-column prop="count" label="出现次数" width="100" />
      </el-table>
      <template #footer>
        <el-button @click="suggestDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!checked.length" @click="addSuggestions(checked); checked = []">添加所选 ({{ checked.length }})</el-button>
      </template>
    </el-dialog>
  </AppShell>
</template>

<style scoped>
.toolbar { padding: 14px; margin-bottom: 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.toolbar :deep(.el-input) { max-width: 320px; }
.toolbar span { color: var(--text-muted); }
.table-wrap { overflow: auto; }
</style>
