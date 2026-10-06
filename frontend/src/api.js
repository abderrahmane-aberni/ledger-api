const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function authHeaders() {
  const token = localStorage.getItem('myaccountant_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...authHeaders(),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export function signup(email, password) {
  return request('/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export async function login(email, password) {
  const form = new URLSearchParams()
  form.set('username', email)
  form.set('password', password)
  const res = await fetch(`${BASE_URL}/login`, { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || 'Login failed')
  }
  const data = await res.json()
  localStorage.setItem('myaccountant_token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('myaccountant_token')
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem('myaccountant_token'))
}

export function listCategories() {
  return request('/categories/')
}

export function createCategory(name) {
  return request('/categories/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function listTransactions() {
  return request('/transactions/')
}

export function createTransaction(tx) {
  return request('/transactions/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tx),
  })
}

export function deleteTransaction(id) {
  return request(`/transactions/${id}`, { method: 'DELETE' })
}

export function monthlySummary() {
  return request('/reports/monthly-summary')
}

export function categoryBreakdown() {
  return request('/reports/category-breakdown')
}

export function budgetAlerts() {
  return request('/reports/budget-alerts')
}

export function rangeSummary(range) {
  return request(`/reports/summary?range=${encodeURIComponent(range)}`)
}
