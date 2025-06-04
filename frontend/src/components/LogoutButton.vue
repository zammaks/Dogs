<template>
  <button @click="logout" class="logout-button">
    Выйти из аккаунта
  </button>
</template>

<script>
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'LogoutButton',
  setup() {
    const store = useStore()
    const router = useRouter()

    const logout = async () => {
      await store.dispatch('auth/logout')
      router.push('/login')
    }

    return {
      logout
    }
  }
}
</script>

<style scoped>
.logout-button {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.logout-button:hover {
  opacity: 0.9;
}
</style> 