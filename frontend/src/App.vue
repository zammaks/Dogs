<template>
  <div id="app">
    <nav class="navbar">
      <router-link to="/" class="nav-brand">DogSitters</router-link>
      <div class="nav-links">
        <template v-if="isAuthenticated">
          <router-link to="/dogsitters">Догситтеры</router-link>
          <router-link to="/bookings">Мои бронирования</router-link>
          <router-link to="/profile" class="user-info">
            {{ currentUser?.first_name }} {{ currentUser?.last_name }}
          </router-link>
          <LogoutButton />
        </template>
        <template v-else>
          <router-link to="/login">Войти</router-link>
          <router-link to="/register">Регистрация</router-link>
        </template>
      </div>
    </nav>
    <router-view></router-view>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import LogoutButton from './components/LogoutButton.vue'

export default {
  name: 'App',
  components: {
    LogoutButton
  },
  setup() {
    const store = useStore()
    const isAuthenticated = computed(() => !!store.state.auth.token)
    const currentUser = computed(() => store.state.auth.user)

    return {
      isAuthenticated,
      currentUser
    }
  }
}
</script>

<style>
#app {
  font-family: Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: #42b983;
  color: white;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.nav-links a:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.user-info {
  color: white;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.2);
}
</style> 