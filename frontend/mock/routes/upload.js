import { UPLOADS, getNextUploadId } from '../db.js'
import { getCurrentUser, parseMultipartFile } from '../utils.js'

const MAX_SIZE = 10 * 1024 * 1024
const ALLOWED_TYPES = new Set([
  'image/jpeg', 'image/png', 'image/webp', 'application/pdf',
  'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
])

function canUpload(user) {
  return user && ['publisher', 'admin'].includes(user.role)
}

export default [
  {
    method: 'POST', path: '/api/uploads', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      if (!canUpload(user)) return { __status: 403, message: '只有发布者和管理员可以上传附件' }
      const file = await parseMultipartFile(req)
      if (!file) return { __status: 422, message: '请选择要上传的文件' }
      if (!ALLOWED_TYPES.has(file.type)) return { __status: 415, message: '不支持的附件格式' }
      if (file.size > MAX_SIZE) return { __status: 413, message: '单个附件不能超过 10 MB' }
      const id = getNextUploadId()
      const attachment = { id, name: file.name, url: `/api/uploads/${id}/content`, mime_type: file.type, size: file.size }
      UPLOADS.set(id, { ...attachment, owner_id: user.id, buffer: file.buffer })
      return attachment
    },
  },
  {
    method: 'DELETE', path: '/api/uploads/:id', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      const upload = UPLOADS.get(req.params.id)
      if (!upload) return { __status: 404, message: '附件不存在' }
      if (user.role !== 'admin' && upload.owner_id !== user.id) return { __status: 403, message: '无权删除该附件' }
      UPLOADS.delete(req.params.id)
      return { success: true }
    },
  },
  {
    method: 'GET', path: '/api/uploads/:id/content', handler: async (req) => {
      const upload = UPLOADS.get(req.params.id)
      if (!upload) return { __status: 404, message: '附件不存在或已删除' }
      return {
        __raw: upload.buffer,
        __contentType: upload.mime_type,
        __headers: { 'Content-Disposition': `inline; filename*=UTF-8''${encodeURIComponent(upload.name)}` },
      }
    },
  },
]
