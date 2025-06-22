<template>
  <div class="auth-callback">
    <div v-if="loading" class="loading-spinner"></div>
    <p v-if="loading">Выполняется авторизация...</p>
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import AuthService from '../services/auth.service';

export default {
  name: 'AuthCallback',
  setup() {
    const router = useRouter();
    const store = useStore();
    const error = ref(null);
    const loading = ref(true);

    onMounted(async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const savedState = localStorage.getItem('oauth_state');

        console.log('Received state:', state);
        console.log('Saved state:', savedState);
        
        if (!code) {
          throw new Error('Код авторизации не получен');
        }

        if (!state || !savedState) {
          throw new Error('Параметр state отсутствует');
        }

        if (state !== savedState) {
          throw new Error('Ошибка проверки безопасности: несоответствие state');
        }

        const success = await store.dispatch('auth/handleYandexCallback', code);
        
        if (success) {
          localStorage.removeItem('oauth_state');
          router.push('/profile');
        } else {
          throw new Error('Не удалось выполнить авторизацию');
        }
      } catch (e) {
        console.error('Auth error:', e);
        error.value = e.message || 'Произошла ошибка при авторизации';
        router.push({
          path: '/login',
          query: { error: error.value }
        });
      } finally {
        loading.value = false;
      }
    });

    return {
      error,
      loading
    };
  }
};
</script>

<style scoped>
.auth-callback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

.error-message {
  color: #dc3545;
  padding: 1rem;
  background-color: #f8d7da;
  border-radius: 4px;
  margin-top: 1rem;
  text-align: center;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 