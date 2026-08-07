import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../store/authStore'

type RetryableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean }

export const api = axios.create({ baseURL: '/api' })

// Anexa o access token em toda request.
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

// Evita disparar N refreshes em paralelo se várias requests tomarem 401 juntas.
let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refreshToken = useAuthStore.getState().refreshToken
  if (!refreshToken) throw new Error('Sem refresh token')

  // axios "cru" (não `api`) pra não entrar de novo no interceptor de request/response
  const { data } = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
  useAuthStore.getState().setTokens({ accessToken: data.access_token, refreshToken: data.refresh_token })
  return data.access_token as string
}

// Se uma request tomar 401 (access token expirado), tenta renovar com o
// refresh token uma vez e repetir a request original. Se o refresh também
// falhar, desloga.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined
    const isAuthEndpoint = originalRequest?.url?.startsWith('/auth/')

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true
      try {
        refreshPromise ??= refreshAccessToken()
        const newToken = await refreshPromise
        refreshPromise = null
        originalRequest.headers.set('Authorization', `Bearer ${newToken}`)
        return api(originalRequest)
      } catch (refreshError) {
        refreshPromise = null
        useAuthStore.getState().logout()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)
