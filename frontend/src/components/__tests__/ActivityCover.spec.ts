import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ActivityCover from '../ActivityCover.vue'

describe('ActivityCover', () => {
  it('renders the real cover image when src is a safe url', () => {
    const wrapper = mount(ActivityCover, {
      props: { src: 'https://example.edu.cn/cover.jpg', category: '讲座', alt: '活动封面' },
    })
    const img = wrapper.find('img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('https://example.edu.cn/cover.jpg')
    expect(img.attributes('loading')).toBe('lazy')
    expect(wrapper.find('.cover-placeholder').exists()).toBe(false)
    wrapper.unmount()
  })

  it('renders a category placeholder with label and watermark glyph when src is missing', () => {
    const wrapper = mount(ActivityCover, { props: { src: null, category: '晚会' } })
    expect(wrapper.find('img').exists()).toBe(false)
    const placeholder = wrapper.find('.cover-placeholder')
    expect(placeholder.exists()).toBe(true)
    expect(placeholder.text()).toContain('晚会')
    expect(wrapper.find('.cover-glyph').text()).toBe('晚')
    wrapper.unmount()
  })

  it('rejects unsafe urls and shows the placeholder instead', () => {
    const wrapper = mount(ActivityCover, {
      props: { src: 'javascript:alert(1)', category: '讲座' },
    })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.cover-placeholder').exists()).toBe(true)
    wrapper.unmount()
  })

  it('falls back to the placeholder when the image fails to load', async () => {
    const wrapper = mount(ActivityCover, {
      props: { src: 'https://example.edu.cn/broken.jpg', category: '展览' },
    })
    await wrapper.find('img').trigger('error')
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.cover-placeholder').exists()).toBe(true)
    wrapper.unmount()
  })
})
