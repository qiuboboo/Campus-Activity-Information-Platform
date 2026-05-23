import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ActivityDetail from '../ActivityDetail.vue'
import { getActivityById } from '@/api/activities'

const replace = vi.fn()
const back = vi.fn()

vi.mock('@/api/activities', () => ({
  getActivityById: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  useRouter: () => ({ replace, back }),
}))

const mockedGetActivityById = vi.mocked(getActivityById)

describe('ActivityDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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
        stubs: {
          'el-button': { template: '<button><slot /></button>' },
          'el-skeleton': { template: '<div class="skeleton"></div>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-icon': { template: '<i><slot /></i>' },
          'el-empty': { template: '<div class="empty"></div>' },
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
  })
})
