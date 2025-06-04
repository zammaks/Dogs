<template>
  <div class="register-container">
    <h2>Регистрация</h2>
    <form @submit.prevent="handleRegister" class="register-form">
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
        <input
          type="password"
          id="password"
          v-model="password"
          required
          class="form-input"
        />
      </div>
      <div class="form-group">
        <label for="firstName">Имя:</label>
        <input
          type="text"
          id="firstName"
          v-model="firstName"
          required
          class="form-input"
        />
      </div>
      <div class="form-group">
        <label for="lastName">Фамилия:</label>
        <input
          type="text"
          id="lastName"
          v-model="lastName"
          required
          class="form-input"
        />
      </div>
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      <button type="submit" class="submit-button">
        Зарегистрироваться
      </button>
      <div class="login-link">
        Уже есть аккаунт? <router-link to="/login">Войдите</router-link>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'Register',
  setup() {
    const store = useStore()
    const router = useRouter()
    const email = ref('')
    const password = ref('')
    const firstName = ref('')
    const lastName = ref('')
    const error = computed(() => store.state.auth.error)

    const handleRegister = async () => {
      const success = await store.dispatch('auth/register', {
        email: email.value,
        password: password.value,
        first_name: firstName.value,
        last_name: lastName.value
      })

      if (success) {
        router.push('/login')
      }
    }

    return {
      email,
      password,
      firstName,
      lastName,
      error,
      handleRegister
    }
  }
}
</script>

<style scoped>
.register-container {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
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

.submit-button:hover {
  background-color: #3aa876;
}

.login-link {
  margin-top: 1rem;
  text-align: center;
  color: var(--text-color);
}

.login-link a {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: bold;
}

.login-link a:hover {
  text-decoration: underline;
}
</style> 