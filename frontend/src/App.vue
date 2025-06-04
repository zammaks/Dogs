<template>
  <div id="app">
    <nav class="navbar">
      <router-link to="/" class="nav-brand">DogSitters</router-link>
      <button class="burger-menu" @click="isMenuOpen = !isMenuOpen">
        <span></span>
        <span></span>
        <span></span>
      </button>
      <div class="nav-links" :class="{ 'nav-open': isMenuOpen }">
        <template v-if="isAuthenticated">
          <router-link to="/" @click="closeMenu">Главная</router-link>
          <router-link to="/dogsitters" @click="closeMenu">Догситтеры</router-link>
          <router-link to="/my-animals" @click="closeMenu">Мои животные</router-link>
          <router-link to="/bookings" @click="closeMenu">Мои бронирования</router-link>
          <router-link to="/profile" class="user-info" @click="closeMenu">
            {{ currentUser?.first_name }} {{ currentUser?.last_name }}
          </router-link>
          <LogoutButton @click="closeMenu" />
        </template>
        <template v-else>
          <router-link to="/login" @click="closeMenu">Войти</router-link>
          <router-link to="/register" @click="closeMenu">Регистрация</router-link>
        </template>
      </div>
    </nav>
    <router-view></router-view>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
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
    const isMenuOpen = ref(false)

    const closeMenu = () => {
      isMenuOpen.value = false
    }

    return {
      isAuthenticated,
      currentUser,
      isMenuOpen,
      closeMenu
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

.burger-menu {
  display: none;
  flex-direction: column;
  justify-content: space-between;
  width: 30px;
  height: 20px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  z-index: 10;
}

.burger-menu span {
  width: 100%;
  height: 2px;
  background-color: white;
  transition: all 0.3s ease;
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

@media (max-width: 768px) {
  .burger-menu {
    display: flex;
  }

  .nav-links {
    display: none;
    position: fixed;
    top: 60px;
    left: 0;
    right: 0;
    flex-direction: column;
    background-color: #42b983;
    padding: 1rem;
    gap: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .nav-links.nav-open {
    display: flex;
  }

  .nav-links a {
    width: 100%;
    text-align: center;
    padding: 0.8rem;
  }

  .user-info {
    justify-content: center;
  }
}
</style> 