import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE_URL })

// attach token to every request
api.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem('arogyamitra-auth')
    if (stored) {
      const parsed = JSON.parse(stored)
      const token = parsed?.state?.token
      if (token) config.headers.Authorization = `Bearer ${token}`
    }
  } catch (e) { }
  return config
})

// handle 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('arogyamitra-auth')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  register: (data) => api.post('/api/auth/register', data),
  login: (data) => api.post('/api/auth/login', data),
  me: () => api.get('/api/auth/me'),
}

export const workoutApi = {
  generate: () => api.post('/api/workouts/generate'),
  getCurrent: () => api.get('/api/workouts/current'),
  getToday: () => api.get('/api/workouts/today'),
  complete: (data) => api.post('/api/workouts/complete', data),
  getHistory: () => api.get('/api/workouts/history'),
  youtubeSearch: (q) => api.get(`/api/workouts/youtube-search?q=${encodeURIComponent(q)}`),
}

export const nutritionApi = {
  generate: (data) => api.post('/api/nutrition/generate', data),
  getCurrent: () => api.get('/api/nutrition/current'),
  getToday: () => api.get('/api/nutrition/today'),
  completeMeal: (data) => api.post('/api/nutrition/meal/complete', data),
  swapMeal: (data) => api.post('/api/nutrition/meal/swap', data),
  getShoppingList: () => api.get('/api/nutrition/shopping-list'),
}

export const progressApi = {
  getSummary: () => api.get('/api/progress/summary'),
  getHistory: (period) => api.get(`/api/progress/history?period=${period}`),
  log: (data) => api.post('/api/progress/log', data),
  getAchievements: () => api.get('/api/progress/achievements'),
  getCharts: () => api.get('/api/progress/charts'),
}

export const chatApi = {
  send: (data) => api.post('/api/aromi-chat', data),
  getHistory: () => api.get('/api/chat-history'),
  adjustPlan: (data) => api.post('/api/adjust-plan', data),
}

export default api