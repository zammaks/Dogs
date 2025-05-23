<template>
  <button @click="handleLogout" class="logout-button">
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

    const handleLogout = () => {
      store.dispatch('auth/logout')
      router.push('/login')
    }

    return {
      handleLogout
    }
  }
}
</script>

<style scoped>
.logout-button {
  padding: 8px 16px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background-color: #c82333;
}
</style> 