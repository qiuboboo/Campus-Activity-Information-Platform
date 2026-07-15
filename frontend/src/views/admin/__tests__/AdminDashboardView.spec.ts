import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AdminDashboardView from '../AdminDashboardView.vue'
import { getAdminSummary } from '@/api/admin'

vi.mock('@/api/admin', () => ({
  getAdminSummary: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

const mockedGetAdminSummary = vi.mocked(getAdminSummary)

const summary = {
  pending: 3,
  published: 12,
  sources: 2,
  failed_tasks: 0,
  posters: { total: 20, published: 12, draft: 4, rejected: 1 },
  knowledge_nodes: 33,
  poster_links: 18,
  data_sources: 2,
  last_crawl: {
    id: 7,
    data_source_id: 1,
    status: 'success',
    pages_found: 10,
    pages_succeeded: 9,
    pages_failed: 1,
    duplicates_skipped: 2,
    drafts_created: 6,
    average_quality_score: 75,
    started_at: '2026-07-15T12:00:00',
    finished_at: '2026-07-15T12:03:00',
  },
}

const mountView = () =>
  mount(AdminDashboardView, {
    global: {
      stubs: {
        AppShell: { template: '<div><slot /></div>' },
        PageState: { template: '<div><slot /></div>' },
        'el-button': { template: '<button><slot /></button>' },
        'el-tag': { template: '<span><slot /></span>' },
        'el-progress': true,
        'el-empty': { template: '<div class="empty"></div>' },
      },
    },
  })

describe('AdminDashboardView 状态分布与爬取面板', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedGetAdminSummary.mockResolvedValue({ data: summary } as any)
  })

  it('renders a status distribution row per workflow state with direct value labels', async () => {
    const wrapper = mountView()
    await flushPromises()

    const rows = wrapper.findAll('.status-row')
    expect(rows.length).toBe(4)
    const text = wrapper.text()
    for (const label of ['已发布', '待审核', '草稿', '已驳回']) expect(text).toContain(label)
    // 直接数值标注
    expect(rows.map((r) => r.text()).join(' ')).toContain('12')
    // 条形宽度按数量比例 (已发布 12/12 = 100%)
    const publishedBar = rows[0].find('.status-bar-fill')
    expect(publishedBar.attributes('style')).toContain('100%')
    wrapper.unmount()
  })

  it('renders the last crawl facts panel', async () => {
    const wrapper = mountView()
    await flushPromises()

    const panel = wrapper.find('.crawl-panel')
    expect(panel.exists()).toBe(true)
    expect(panel.text()).toContain('9')  // pages_succeeded
    expect(panel.text()).toContain('6')  // drafts_created
    wrapper.unmount()
  })

  it('shows an empty state when there is no crawl yet', async () => {
    mockedGetAdminSummary.mockResolvedValue({ data: { ...summary, last_crawl: null } } as any)
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.crawl-panel .empty').exists()).toBe(true)
    wrapper.unmount()
  })
})
