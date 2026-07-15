import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import HomeCalendarCard from './HomeCalendarCard.vue'

describe('HomeCalendarCard', () => {
  it('keeps non-current-month dates out of keyboard interaction', async () => {
    const outsideDate = new Date(2026, 5, 30)
    const wrapper = mount(HomeCalendarCard, {
      props: {
        currentYear: 2026,
        currentMonth: 6,
        weekDays: ['日', '一', '二', '三', '四', '五', '六'],
        calendarDays: [{ date: outsideDate, isCurrentMonth: false, isToday: false, isSelected: false }],
        selectedDate: new Date(2026, 6, 1),
        scheduleItems: [],
      },
      global: { stubs: { 'el-icon': true, 'el-button': true, 'el-empty': true, 'el-alert': true } },
    })
    const button = wrapper.get('button.cal-other')
    expect(button.attributes('disabled')).toBeDefined()
    await button.trigger('click')
    expect(wrapper.emitted('selectDate')).toBeUndefined()
  })
})
