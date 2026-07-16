import axios from 'axios'

// Read the backend URL from the build-time env var so production bundles can point
// at a real backend. Vite inlines import.meta.env.VITE_API_BASE_URL at build time;
// when it is unset (the local dev default) we fall back to the localhost backend.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api'

// Single configured axios instance shared by every method below. Centralizing the
// base URL, a request timeout, and error handling here keeps each method thin and
// gives every request identical behavior. Methods use paths relative to baseURL.
const http = axios.create({
  baseURL: API_BASE_URL,
  // Fail fast instead of hanging indefinitely if the backend is unreachable.
  timeout: 10000,
})

// Centralized error handling: log once here (so call sites don't each duplicate it),
// then rethrow so component-level try/catch still runs and can render its error state.
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url
    console.error(
      `API request failed${status ? ` (${status})` : ''}${url ? ` for ${url}` : ''}:`,
      error.message
    )
    return Promise.reject(error)
  }
)

export const api = {
  async getInventory(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)

    const response = await http.get(`/inventory?${params.toString()}`)
    return response.data
  },

  async getInventoryItem(id) {
    const response = await http.get(`/inventory/${encodeURIComponent(id)}`)
    return response.data
  },

  async getOrders(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await http.get(`/orders?${params.toString()}`)
    return response.data
  },

  async getOrder(id) {
    const response = await http.get(`/orders/${encodeURIComponent(id)}`)
    return response.data
  },

  async getDemandForecasts() {
    const response = await http.get(`/demand`)
    return response.data
  },

  async getBacklog() {
    const response = await http.get(`/backlog`)
    return response.data
  },

  async getRestockingRecommendations(budget) {
    const response = await http.get(`/restocking/recommendations`, {
      params: { budget }
    })
    return response.data
  },

  async placeRestockingOrder(items) {
    const response = await http.post(`/restocking/orders`, { items })
    return response.data
  },

  async getDashboardSummary(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await http.get(`/dashboard/summary?${params.toString()}`)
    return response.data
  },

  async getSpendingSummary() {
    const response = await http.get(`/spending/summary`)
    return response.data
  },

  async getMonthlySpending() {
    const response = await http.get(`/spending/monthly`)
    return response.data
  },

  async getCategorySpending() {
    const response = await http.get(`/spending/categories`)
    return response.data
  },

  async getTransactions() {
    const response = await http.get(`/spending/transactions`)
    return response.data
  },

  async getTasks() {
    const response = await http.get(`/tasks`)
    return response.data
  },

  async createTask(taskData) {
    const response = await http.post(`/tasks`, taskData)
    return response.data
  },

  async deleteTask(taskId) {
    const response = await http.delete(`/tasks/${encodeURIComponent(taskId)}`)
    return response.data
  },

  async toggleTask(taskId) {
    const response = await http.patch(`/tasks/${encodeURIComponent(taskId)}`)
    return response.data
  },

  async createPurchaseOrder(purchaseOrderData) {
    const response = await http.post(`/purchase-orders`, purchaseOrderData)
    return response.data
  },

  async getPurchaseOrderByBacklogItem(backlogItemId) {
    const response = await http.get(`/purchase-orders/${encodeURIComponent(backlogItemId)}`)
    return response.data
  },

  async getQuarterlyReports() {
    const response = await http.get(`/reports/quarterly`)
    return response.data
  },

  async getMonthlyTrends() {
    const response = await http.get(`/reports/monthly-trends`)
    return response.data
  }
}
