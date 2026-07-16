/**
 * Safely sanitize an HTML string for v-html rendering.
 * Strips script/iframe/object/embed/link/style tags, on* attributes,
 * and javascript: URLs. No external dependencies.
 */
export function sanitizeHtml(value?: string | null): string {
  if (!value || typeof window === 'undefined') return ''
  const doc = new DOMParser().parseFromString(value, 'text/html')
  doc.querySelectorAll('script, iframe, object, embed, link, style').forEach((node) => node.remove())
  doc.body.querySelectorAll('*').forEach((node) => {
    for (const attr of [...node.attributes]) {
      const name = attr.name.toLowerCase()
      const attrValue = attr.value.trim().toLowerCase()
      if (name.startsWith('on') || attrValue.startsWith('javascript:')) node.removeAttribute(attr.name)
    }
  })
  return doc.body.innerHTML
}
