const API_PREFIX = '/api'
const WRITE_METHODS = new Set(['POST', 'PATCH', 'DELETE'])

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function getCookie(name) {
  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${encodeURIComponent(name)}=`))

  return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : null
}

function apiPath(path) {
  if (path.startsWith('/api/')) return path
  return `${API_PREFIX}${path.startsWith('/') ? path : `/${path}`}`
}

export async function apiRequest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const headers = new Headers(options.headers)
  const requestOptions = {
    ...options,
    method,
    headers,
    credentials: 'include',
  }

  if (options.body !== undefined && options.body !== null) {
    headers.set('Content-Type', 'application/json')
    requestOptions.body = JSON.stringify(options.body)
  }

  if (WRITE_METHODS.has(method)) {
    const csrfToken = getCookie('swampspace_csrf')
    if (csrfToken) headers.set('X-CSRF-Token', csrfToken)
  }

  const response = await fetch(apiPath(path), requestOptions)
  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json')
    ? await response.json()
    : null

  if (!response.ok) {
    throw new ApiError(
      Array.isArray(data?.detail)
        ? data.detail.map(item => `${item.loc?.slice(1).join('.') || 'Form'}: ${item.msg}`).join('; ')
        : data?.detail || `Request failed with status ${response.status}`,
      response.status,
      data,
    )
  }

  return data
}

export const api = {
  get: (path, options) => apiRequest(path, { ...options, method: 'GET' }),
  post: (path, body, options) =>
    apiRequest(path, { ...options, method: 'POST', body }),
  patch: (path, body, options) =>
    apiRequest(path, { ...options, method: 'PATCH', body }),
  delete: (path, options) => apiRequest(path, { ...options, method: 'DELETE' }),
}
