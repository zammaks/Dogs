import { endpoints, getHeaders } from '../api/config'

export default {
  namespaced: true,
  state: {
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    error: null
  },
  mutations: {
    setUser(state, user) {
      state.user = user
      if (user) {
        localStorage.setItem('user', JSON.stringify(user))
      } else {
        localStorage.removeItem('user')
      }
    },
    setToken(state, token) {
      state.token = token
      if (token) {
        localStorage.setItem('token', token)
      } else {
        localStorage.removeItem('token')
      }
    },
    setError(state, error) {
      state.error = error
    }
  },
  actions: {
    async login({ commit }, credentials) {
      try {
        commit('setError', null)
        const response = await fetch(endpoints.login, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify(credentials)
        })
        
        const data = await response.json()
        console.log('Login response:', data)
        
        if (!response.ok) {
          commit('setError', data.message || 'Неверный email или пароль')
          return false
        }

        commit('setToken', data.token)
        commit('setUser', data.user)
        console.log('User data after login:', data.user)
        return true
      } catch (error) {
        console.error('Login error:', error)
        commit('setError', 'Ошибка сервера')
        return false
      }
    },

    async register({ commit }, userData) {
      try {
        commit('setError', null)
        const response = await fetch(endpoints.register, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify(userData)
        })
        
        const data = await response.json()
        
        if (!response.ok) {
          commit('setError', data.message || 'Ошибка регистрации')
          return false
        }

        return true
      } catch (error) {
        console.error('Registration error:', error)
        commit('setError', 'Ошибка сервера')
        return false
      }
    },
    
    logout({ commit }) {
      commit('setToken', null)
      commit('setUser', null)
      commit('setError', null)
    }
  },
  getters: {
    isAuthenticated: state => !!state.token,
    currentUser: state => state.user,
    error: state => state.error
  }
} 