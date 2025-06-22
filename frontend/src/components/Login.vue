<template>
  <div class="login-container">
    <div class="login-box">
      <h2>Вход в систему</h2>
      <div v-if="error" class="error-message">{{ error }}</div>
      
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
        
        <!-- Кнопка обычного входа -->
        <button 
          type="submit" 
          class="login-button"
          :disabled="loading"
        >
          <span v-if="loading">Вход...</span>
          <span v-else>Войти</span>
        </button>
        
        <!-- Разделитель -->
        <div class="divider">
          <span>или</span>
        </div>
        
        <!-- Кнопка входа через Яндекс -->
        <button 
          type="button" 
          @click="handleYandexLogin" 
          class="yandex-button"
          :disabled="yandexLoading"
        >
          <span v-if="yandexLoading">Подключение...</span>
          <span v-else>Войти через Яндекс</span>
        </button>
        
        <div class="register-link">
          Нет аккаунта? <router-link to="/register">Зарегистрируйтесь</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import AuthService from '../services/auth.service'

export default {
  name: 'Login',
  setup() {
    const store = useStore()
    const router = useRouter()
    const email = ref('')
    const password = ref('')
    const loading = ref(false)
    const yandexLoading = ref(false)
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

    const handleYandexLogin = async () => {
      try {
        yandexLoading.value = true;
        await AuthService.initiateYandexAuth();
      } catch (error) {
        console.error('Ошибка при входе через Яндекс:', error);
        error.value = 'Не удалось начать процесс авторизации через Яндекс';
      } finally {
        yandexLoading.value = false;
      }
    }

    return {
      email,
      password,
      error,
      loading,
      yandexLoading,
      showPassword,
      handleLogin,
      handleYandexLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.login-box {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.error-message {
  color: #dc3545;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: #f8d7da;
  border-radius: 4px;
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

.oauth-buttons {
  margin-top: 1rem;
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.login-button:hover:not(:disabled) {
  background-color: #0056b3;
}

.login-button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.login-button:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.3);
}

.divider {
  display: flex;
  align-items: center;
  margin: 1rem 0;
  color: #6c757d;
  font-size: 0.9rem;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background-color: #dee2e6;
}

.divider span {
  padding: 0 1rem;
  background-color: white;
}

.yandex-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #fc3f1d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.yandex-button:hover:not(:disabled) {
  background-color: #eb3517;
}

.yandex-button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.yandex-button:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(252, 63, 29, 0.3);
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