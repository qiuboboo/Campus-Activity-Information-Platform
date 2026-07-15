import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'
import ActivityDetail from '../ActivityDetail.vue'
import { getActivityById } from '@/api/activities'
import { createPinia } from 'pinia'

const replace = vi.fn()
const back = vi.fn()
const route = reactive({ params: { id: '1' }, query: {} as Record<string, string> })

vi.mock('@/api/activities', () => ({
  getActivityById: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ replace, back, push: vi.fn() }),
}))

const mockedGetActivityById = vi.mocked(getActivityById)

describe('ActivityDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    route.params.id = '1'
    mockedGetActivityById.mockResolvedValue({
      data: {
        id: 1,
        title: '中山大学第12届学术科技节',
        raw_text: '活动正文内容',
        summary: '综合性学术活动',
        event_time: '2026-06-15T09:00:00',
        location: '广州校区南校园',
        organizer: '中山大学团委',
        status: 'published',
        activity_type: '讲座',
        created_at: '2026-05-20T10:00:00',
        tags: ['学术', '公开'],
        attachments: [],
        meta: { views: 128, registrations: 36 },
      },
    } as any)
  })

  it('renders title and time from the activity detail data', async () => {
    const wrapper = mount(ActivityDetail, {
      global: {
        plugins: [createPinia()],
        stubs: {
          AppShell: { template: '<div><slot /></div>' },
          'el-button': { template: '<button><slot /></button>' },
          'el-skeleton': { template: '<div class="skeleton"></div>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-icon': { template: '<i><slot /></i>' },
          'el-empty': { template: '<div class="empty"></div>' },
          'el-result': { template: '<div class="result"><slot /></div>' },
        },
      },
    })

    await flushPromises()

    const expectedTime = new Date('2026-06-15T09:00:00').toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })

    expect(wrapper.text()).toContain('中山大学第12届学术科技节')
    expect(wrapper.text()).toContain(expectedTime)
    wrapper.unmount()
  })

  it('reloads when navigating to another activity through the reused route', async () => {
    mockedGetActivityById.mockReset()
    mockedGetActivityById.mockResolvedValueOnce({ data: { id: 1, title: '活动一', raw_text: '', summary: '', event_time: null, location: null, organizer: null, status: 'published', activity_type: null, created_at: '2026-01-01T00:00:00' } } as any)
      .mockResolvedValueOnce({ data: { id: 2, title: '活动二', raw_text: '', summary: '', event_time: null, location: null, organizer: null, status: 'published', activity_type: null, created_at: '2026-01-01T00:00:00' } } as any)
    const wrapper = mount(ActivityDetail, { global: { plugins: [createPinia()], stubs: { AppShell: { template: '<div><slot /></div>' }, 'el-button': { template: '<button><slot /></button>' }, 'el-skeleton': true, 'el-tag': true, 'el-icon': true, 'el-empty': true, 'el-result': true } } })
    await flushPromises()
    route.params.id = '2'
    await flushPromises()
    expect(mockedGetActivityById).toHaveBeenLastCalledWith(2)
    expect(wrapper.text()).toContain('活动二')
    wrapper.unmount()
  })
})
