import { clearAccessToken, getAccessToken } from '../stores/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const VALIDATION_FIELD_LABELS = {
  email: 'Email',
  password: 'Пароль',
  password_confirmation: 'Подтверждение пароля',
  current_password: 'Текущий пароль',
  new_password: 'Новый пароль',
  new_password_confirmation: 'Подтверждение нового пароля',
}

function formatValidationDetail(item) {
  const field = item?.loc?.[item.loc.length - 1]
  const label = VALIDATION_FIELD_LABELS[field] || field
  return label ? `${label}: ${item.msg}` : item.msg
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  const token = getAccessToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    clearAccessToken()
  }

  let body = null
  const contentType = response.headers.get('content-type') || ''
  const contentLength = response.headers.get('content-length')
  const hasBody = response.status !== 204 && response.status !== 205 && contentLength !== '0'

  if (hasBody && contentType.includes('application/json')) {
    const responseText = await response.text()
    body = responseText ? JSON.parse(responseText) : null
  }

  if (!response.ok) {
    const detail = Array.isArray(body?.detail)
      ? body.detail.map(formatValidationDetail).join('. ')
      : body?.detail || 'Request failed'
    throw new Error(detail)
  }

  return body
}

export const api = {
  register(payload) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: payload.email.trim().toLowerCase(),
        password: payload.password,
        password_confirmation: payload.password_confirmation,
      }),
    })
  },
  login(payload) {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email: payload.email.trim().toLowerCase(),
        password: payload.password,
      }),
    })
  },
  getProfile() {
    return request('/profile')
  },
  refreshKey() {
    return request('/profile/refresh-key', {
      method: 'POST',
    })
  },
  changePassword(payload) {
    return request('/profile/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: payload.current_password,
        new_password: payload.new_password,
        new_password_confirmation: payload.new_password_confirmation,
      }),
    })
  },
}
