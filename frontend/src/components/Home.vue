<template>
  <div class="home-container">
    <div class="welcome-section">
      <h1 class="welcome-message" v-if="currentUser">
        Привет, {{ currentUser.first_name }}!
      </h1>
      <p class="welcome-subtitle">Добро пожаловать в систему поиска догситтеров</p>
    </div>
    
    <div class="content">
      <div class="nav-card" @click="navigateTo('DogSitters')">
        <div class="card-icon">🐕</div>
        <h3>Найти догситтера</h3>
        <p>Просмотр списка доступных догситтеров</p>
      </div>
      
      <div class="nav-card" @click="navigateTo('Bookings')">
        <div class="card-icon">📅</div>
        <h3>Мои бронирования</h3>
        <p>История ваших бронирований</p>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'Home',
  setup() {
    const store = useStore()
    const router = useRouter()
    const currentUser = computed(() => store.state.auth.user)

    const navigateTo = (routeName) => {
      router.push({ name: routeName })
    }

    return {
      currentUser,
      navigateTo
    }
  }
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.welcome-section {
  text-align: center;
  margin-bottom: 3rem;
}

.welcome-message {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.welcome-subtitle {
  font-size: 1.2rem;
  color: #666;
}

.content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.nav-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  border: 2px solid #eee;
  transition: all 0.3s ease;
}

.nav-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  border-color: #42b983;
}

.card-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.nav-card h3 {
  color: #42b983;
  margin-bottom: 0.8rem;
  font-size: 1.4rem;
}

.nav-card p {
  color: #666;
  margin: 0;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .home-container {
    padding: 1rem;
  }
  
  .welcome-message {
    font-size: 2rem;
  }
  
  .content {
    grid-template-columns: 1fr;
  }
}
</style> 