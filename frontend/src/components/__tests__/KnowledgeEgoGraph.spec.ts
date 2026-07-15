import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import KnowledgeEgoGraph from '../KnowledgeEgoGraph.vue'

const related = [
  { id: 11, title: 'AI 创新应用讲座', relation: 'same_topic' },
  { id: 12, title: '校园科技文化节开幕式', relation: 'same_place' },
  { id: 13, title: '数学建模竞赛宣讲', relation: 'same_org' },
]

describe('KnowledgeEgoGraph', () => {
  it('renders the center node and one satellite per related activity', () => {
    const wrapper = mount(KnowledgeEgoGraph, {
      props: { centerName: '大学生活动中心', centerType: 'place', related },
    })
    expect(wrapper.find('.ego-center').text()).toContain('大学生活动中心')
    expect(wrapper.findAll('.ego-node').length).toBe(3)
    expect(wrapper.findAll('.ego-edge').length).toBe(3)
    wrapper.unmount()
  })

  it('caps satellites at 10 and reports the overflow count', () => {
    const many = Array.from({ length: 14 }, (_, i) => ({ id: i + 1, title: `活动${i + 1}`, relation: 'same_day' }))
    const wrapper = mount(KnowledgeEgoGraph, {
      props: { centerName: '校团委', centerType: 'organization', related: many },
    })
    expect(wrapper.findAll('.ego-node').length).toBe(10)
    expect(wrapper.text()).toContain('4')
    wrapper.unmount()
  })

  it('emits open with the activity id when a satellite is clicked', async () => {
    const wrapper = mount(KnowledgeEgoGraph, {
      props: { centerName: '校团委', centerType: 'organization', related },
    })
    await wrapper.findAll('.ego-node')[0].trigger('click')
    expect(wrapper.emitted('open')?.[0]).toEqual([11])
    wrapper.unmount()
  })
})
