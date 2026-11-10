/**
 * 后端接口封装
 *
 * 统一处理三件事：
 *   1. 基地址与开发代理 —— baseURL 为 /api，开发模式由 Vite 转发到 Django 8000
 *   2. CSRF —— Django 对写操作强制校验 CSRF，提交前先取一次 token
 *   3. 响应结构 —— 后端统一返回信封格式，这里转换成 { ok, message, data, errors }
 *
 * 接口调用方不需要 try/catch，也不会看到 axios 的原始报错对象。
 */

import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
  // 让 axios 自动读取 csrftoken Cookie 并放进 X-CSRFToken 请求头
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  withCredentials: true,
})

// 缓存下来的 CSRF token
let csrfToken = ''

/**
 * 取一个可用的 CSRF token。
 *
 * 后端 /api/csrf/ 同时会写 csrftoken Cookie 并在响应体里返回 token，
 * 两份都留着：Cookie 供 axios 自动使用，响应体里的用于手动设置请求头。
 */
export async function ensureCsrfToken() {
  if (csrfToken) return csrfToken

  const response = await http.get('/csrf/')
  csrfToken = response.data?.data?.csrfToken || ''
  return csrfToken
}

/** 把成功响应转换成统一结构。 */
function toResult(response) {
  const body = response.data

  // 后端返回的是标准信封
  if (body && typeof body === 'object' && 'success' in body) {
    return {
      ok: Boolean(body.success),
      code: body.code || 'ok',
      message: body.message || '',
      data: body.data ?? null,
      errors: body.errors || null,
      status: response.status,
    }
  }

  // 兜底：后端返回了非信封结构
  return {
    ok: true,
    code: 'ok',
    message: '',
    data: body,
    errors: null,
    status: response.status,
  }
}

/** 把异常转换成统一结构，并保证提示语是中文。 */
function toError(error) {
  const status = error.response?.status || 0
  const body = error.response?.data

  if (body && typeof body === 'object' && 'success' in body) {
    return {
      ok: false,
      code: body.code || 'error',
      message: body.message || '提交失败，请稍后再试。',
      data: null,
      errors: body.errors || null,
      status,
    }
  }

  if (error.code === 'ECONNABORTED') {
    return {
      ok: false,
      code: 'timeout',
      message: '请求超时，请检查网络后重试。',
      data: null,
      errors: null,
      status: 0,
    }
  }

  return {
    ok: false,
    code: 'network_error',
    message: status ? `请求失败（${status}），请稍后再试。` : '网络异常，暂时无法提交，请稍后再试。',
    data: null,
    errors: null,
    status,
  }
}

/**
 * 提交咨询留言。
 *
 * @param {object} payload 表单数据
 * @returns {Promise<{ok: boolean, message: string, data: object|null, errors: object|null}>}
 */
export async function submitContact(payload) {
  const post = async () => {
    await ensureCsrfToken()
    return http.post('/contacts/', payload, {
      headers: { 'X-CSRFToken': csrfToken },
    })
  }

  try {
    return toResult(await post())
  } catch (error) {
    // 403 说明 token 可能已失效（登录状态变化或 Cookie 过期），
    // 刷新一次 token 后重试；公开接口的 403 只可能是 CSRF 校验失败
    if (error.response?.status === 403) {
      csrfToken = ''
      try {
        return toResult(await post())
      } catch (retryError) {
        return toError(retryError)
      }
    }
    return toError(error)
  }
}

/**
 * 查看留言列表（仅管理员登录后可用）。
 *
 * @param {number} page 页码，从 1 开始
 */
export async function fetchContacts(page = 1) {
  try {
    const response = await http.get('/contacts/', { params: { page } })
    const result = toResult(response)
    return result
  } catch (error) {
    return toError(error)
  }
}

export default http
