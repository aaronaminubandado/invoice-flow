import axios, { AxiosError } from 'axios'
import { supabase } from '@/lib/supabase'
import { mapApiErrorDetail } from '@/lib/api-errors'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>
    const status = axiosError.response?.status
    const mapped = mapApiErrorDetail(axiosError.response?.data?.detail, status)
    if (mapped) {
      return mapped
    }
    if (axiosError.response?.status === 409) {
      return 'This action conflicts with existing data. Please refresh and try again.'
    }
    if (axiosError.response?.status === 404) {
      return 'Not found'
    }
    if (axiosError.response?.status === 400) {
      return 'Invalid request. Please check your input and try again.'
    }
    if (axiosError.response?.status === 500) {
      return 'Server error. Please try again later.'
    }
    return axiosError.message || 'An error occurred'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await supabase.auth.signOut()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
