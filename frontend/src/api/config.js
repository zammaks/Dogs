const API_URL = 'http://localhost:8000/api'
const MEDIA_URL = 'http://localhost:8000/media'

export const endpoints = {
  login: `${API_URL}/auth/login/`,
  register: `${API_URL}/auth/register/`,
  dogsitters: `${API_URL}/dogsitters/`,
  bookings: `${API_URL}/bookings/`
}

export const DEFAULT_AVATAR = '/images/default_avatar.jpg'

// Добавляем конфигурацию для заголовков запросов
export const getHeaders = () => {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }

  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return headers
}

import axios from 'axios'
import store from '../store'

// Создаем экземпляр axios с общими настройками
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Добавляем перехватчик для установки токена
api.interceptors.request.use(
  config => {
    const token = store.state.auth.token || localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('Ошибка при подготовке запроса:', error)
    return Promise.reject(error)
  }
)

// Добавляем перехватчик ответов
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      console.log('Ошибка авторизации, перенаправление на страницу входа')
      // Очищаем токен
      localStorage.removeItem('token')
      store.commit('auth/setToken', null)
      // Перенаправляем на страницу входа
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
) 