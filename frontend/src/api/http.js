import axios from 'axios'

export const TOKEN_KEY = 'task_system_token'
export const USER_KEY = 'task_system_user'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

let unauthorizedHandler = null

/** 由 main.js 注册：收到 401 时清理登录态并跳回登录页 */
export function onUnauthorized(handler) {
  unauthorizedHandler = handler
}

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url ?? ''
    const isCredentialRequest = url.includes('/auth/login') || url.includes('/auth/register')
    if (status === 401 && !isCredentialRequest && unauthorizedHandler) {
      unauthorizedHandler()
    }
    return Promise.reject(normalizeError(error))
  },
)

/** 把后端 {detail, code} 与网络异常统一成 {message, code, status}，供界面直接展示 */
export function normalizeError(error) {
  if (!error.response) {
    return { message: '无法连接服务器，请确认后端已启动', code: 'network_error', status: 0 }
  }
  const { status, data } = error.response
  const detail = data?.detail
  let message = '请求失败，请稍后重试'
  if (typeof detail === 'string' && detail) {
    message = detail
  } else if (Array.isArray(detail) && detail.length > 0) {
    message = detail.map((item) => `${item.field}：${item.message}`).join('；')
  }
  return { message, code: data?.code ?? 'http_error', status }
}

export default http
