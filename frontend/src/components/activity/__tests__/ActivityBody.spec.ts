import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ActivityBody from '../ActivityBody.vue'

const globalStubs = {
  stubs: {
    'el-empty': { template: '<div class="empty"></div>' },
  },
}

describe('ActivityBody', () => {
  it('renders only the html version when contentHtml is present (no duplicated raw text)', () => {
    const wrapper = mount(ActivityBody, {
      props: {
        rawText: '纯文本正文',
        contentHtml: '<p>富文本正文</p>',
        attachments: [],
      },
      global: globalStubs,
    })

    expect(wrapper.find('.body-html').exists()).toBe(true)
    expect(wrapper.find('.body-html').html()).toContain('富文本正文')
    // 有富文本时不应再渲染纯文本段落,否则正文显示两遍
    expect(wrapper.find('.body-text').exists()).toBe(false)
    wrapper.unmount()
  })

  it('falls back to raw text when contentHtml is absent', () => {
    const wrapper = mount(ActivityBody, {
      props: { rawText: '纯文本正文', contentHtml: null, attachments: [] },
      global: globalStubs,
    })

    expect(wrapper.find('.body-html').exists()).toBe(false)
    expect(wrapper.find('.body-text').text()).toContain('纯文本正文')
    wrapper.unmount()
  })

  it('strips script tags and event handlers from contentHtml', () => {
    const wrapper = mount(ActivityBody, {
      props: {
        rawText: '',
        contentHtml: '<p onclick="alert(1)">内容</p><script>alert(2)</scr' + 'ipt><img src="x" onerror="alert(3)">',
        attachments: [],
      },
      global: globalStubs,
    })

    const html = wrapper.find('.body-html').html()
    expect(html).toContain('内容')
    expect(html).not.toContain('script')
    expect(html).not.toContain('onclick')
    expect(html).not.toContain('onerror')
    wrapper.unmount()
  })
})
