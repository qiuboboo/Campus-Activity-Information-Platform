import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (!err.response) {
      ElMessage.error('网络连接失败，请检查后端服务是否运行')
      return Promise.reject(err)
    }

    const { status, data } = err.response
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      ElMessage.warning('登录已过期，请重新登录')
      if (!window.location.pathname.startsWith('/auth/')) {
        const redirect = `${window.location.pathname}${window.location.search}${window.location.hash}`
        window.location.assign(`/auth/login?redirect=${encodeURIComponent(redirect)}`)
      }
    } else if (status === 403) {
      ElMessage.error('权限不足')
    } else if (status === 422) {
      ElMessage.error(data?.message || data?.error || '提交内容格式不正确，请检查表单')
    } else if (status === 429) {
      ElMessage.error(data?.message || '请求过于频繁，请稍后再试')
    } else if (status >= 500) {
      ElMessage.error('服务器内部错误')
    } else if (data?.message) {
      ElMessage.error(data.message)
    }
    return Promise.reject(err)
  },
)

export default client
