// Single axios instance every page/hook goes through — a request
// interceptor attaches the JWT, a response interceptor centralizes 401
// handling (clear session, redirect to /login) so no component repeats
// that logic. Requests go through Vite's dev-server proxy (/api/* ->
// backend), so no base URL needs hardcoding in dev.
import axios from 'axios'
import { clearSession, getToken } from '@/lib/auth'

export const apiClient = axios.create({
  baseURL: '/api',
})

apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      clearSession()
      window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)
