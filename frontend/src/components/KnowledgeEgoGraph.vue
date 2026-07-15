<script setup lang="ts">
import { computed } from 'vue'

interface RelatedItem {
  id: number
  title: string
  relation?: string
}

interface Props {
  centerName: string
  centerType?: string
  related: RelatedItem[]
}

const props = defineProps<Props>()
const emit = defineEmits<{ open: [id: number] }>()

const MAX_SATELLITES = 10
const W = 520
const H = 340
const CX = W / 2
const CY = H / 2
const RADIUS = 128

// 节点类型 → 语义色 (与 Dashboard 状态色板同一验证家族)
const TYPE_COLORS: Record<string, string> = {
  place: '#3d78b3',
  organization: '#b5830f',
  topic: '#0e7d4c',
  time: '#5b5f97',
  source: '#a63a34',
}

const centerColor = computed(() => TYPE_COLORS[props.centerType || ''] || '#0d5e3c')

const satellites = computed(() =>
  props.related.slice(0, MAX_SATELLITES).map((item, index, list) => {
    // 从正上方开始均匀放射
    const angle = (2 * Math.PI * index) / list.length - Math.PI / 2
    return {
      ...item,
      x: CX + RADIUS * Math.cos(angle),
      y: CY + RADIUS * Math.sin(angle),
      label: item.title.length > 10 ? `${item.title.slice(0, 10)}…` : item.title,
    }
  }),
)

const overflow = computed(() => Math.max(0, props.related.length - MAX_SATELLITES))

const RELATION_LABELS: Record<string, string> = {
  same_day: '同日',
  same_place: '同地点',
  same_org: '同主办',
  same_topic: '同主题',
}
const relationLabel = (value?: string) => RELATION_LABELS[value || ''] || value || '关联'
</script>

<template>
  <figure class="ego-graph">
    <svg :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="`${centerName} 的关联活动网络`">
      <line
        v-for="node in satellites"
        :key="`edge-${node.id}`"
        class="ego-edge"
        :x1="CX"
        :y1="CY"
        :x2="node.x"
        :y2="node.y"
      />
      <g
        v-for="node in satellites"
        :key="`node-${node.id}`"
        class="ego-node"
        role="button"
        tabindex="0"
        :aria-label="`查看活动：${node.title}`"
        @click="emit('open', node.id)"
        @keyup.enter="emit('open', node.id)"
      >
        <circle :cx="node.x" :cy="node.y" r="7" />
        <text :x="node.x" :y="node.y + (node.y >= CY ? 22 : -14)" text-anchor="middle">
          <title>{{ node.title }}（{{ relationLabel(node.relation) }}）</title>
          {{ node.label }}
        </text>
      </g>
      <g class="ego-center">
        <title>{{ centerName }}</title>
        <circle :cx="CX" :cy="CY" r="34" :fill="centerColor" />
        <text :x="CX" :y="CY + 4" text-anchor="middle">{{ centerName.length > 8 ? `${centerName.slice(0, 8)}…` : centerName }}</text>
      </g>
    </svg>
    <figcaption v-if="overflow" class="ego-overflow">另有 {{ overflow }} 个关联活动未显示,见下方列表</figcaption>
  </figure>
</template>

<style scoped>
.ego-graph { margin: 0; }
.ego-graph svg { width: 100%; height: auto; display: block; }
.ego-edge { stroke: #cdd9d1; stroke-width: 1.5; }
.ego-node { cursor: pointer; }
.ego-node circle { fill: #fff; stroke: var(--brand, #0d5e3c); stroke-width: 2; transition: r 0.15s; }
.ego-node:hover circle, .ego-node:focus circle { fill: var(--brand-soft, #eaf5ee); r: 9; }
.ego-node:focus { outline: none; }
.ego-node:focus circle { stroke-width: 3; }
.ego-node text { font-size: 12px; fill: #37423e; }
.ego-center text { font-size: 13px; font-weight: 700; fill: #fff; }
.ego-overflow { margin-top: 6px; color: #66736d; font-size: 12px; text-align: center; }
</style>
