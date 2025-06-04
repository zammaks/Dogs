<template>
  <div class="login-container">
    <h2>Вход в систему</h2>
    <form @submit.prevent="handleLogin" class="login-form">
      <div class="form-group">
        <label for="email">Email:</label>
        <input
          type="email"
          id="email"
          v-model="email"
          required
          class="form-input"
        />
      </div>
      <div class="form-group">
        <label for="password">Пароль:</label>
        <div class="password-input-container">
          <input
            :type="showPassword ? 'text' : 'password'"
            id="password"
            v-model="password"
            required
            class="form-input"
          />
          <button 
            type="button" 
            class="toggle-password"
            @click="showPassword = !showPassword"
            :title="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              :class="{ 'eye-crossed': !showPassword }"
              class="eye-icon"
            >
              <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
            </svg>
          </button>
        </div>
      </div>
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      <button type="submit" class="submit-button" :disabled="loading">
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>
      <div class="register-link">
        Нет аккаунта? <router-link to="/register">Зарегистрируйтесь</router-link>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'Login',
  setup() {
    const store = useStore()
    const router = useRouter()
    const email = ref('')
    const password = ref('')
    const loading = ref(false)
    const showPassword = ref(false)
    const error = computed(() => store.state.auth.error)

    const handleLogin = async () => {
      try {
        loading.value = true
        const success = await store.dispatch('auth/login', {
          email: email.value,
          password: password.value
        })

        if (success) {
          router.push({ name: 'Home' })
        }
      } catch (err) {
        console.error('Login error:', err)
      } finally {
        loading.value = false
      }
    }

    return {
      email,
      password,
      error,
      loading,
      showPassword,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.password-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.form-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 100%;
}

.toggle-password {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eye-icon {
  width: 24px;
  height: 24px;
  fill: #666;
  transition: fill 0.2s;
}

.eye-icon:hover {
  fill: #333;
}

.eye-crossed {
  opacity: 0.5;
}

.error-message {
  color: #dc3545;
  margin-bottom: 1rem;
}

.submit-button {
  padding: 10px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-button:disabled {
  background-color: #a8d5c2;
  cursor: not-allowed;
}

.submit-button:not(:disabled):hover {
  background-color: #3aa876;
}

.register-link {
  margin-top: 1rem;
  text-align: center;
  color: var(--text-color);
}

.register-link a {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: bold;
}

.register-link a:hover {
  text-decoration: underline;
}
</style> 