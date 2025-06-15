<template>
  <div class="dogsitter-profile">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка профиля догситтера...</p>
    </div>
    
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    
    <div v-else class="profile-content">
      <div class="profile-header">
        <img 
          :src="dogsitter.avatar || '/default-avatar.png'" 
          :alt="dogsitter.first_name"
          class="profile-avatar"
        >
        <div class="profile-info">
          <h1>{{ dogsitter.first_name }} {{ dogsitter.last_name }}</h1>
          <div class="rating">
            <span class="stars">★</span>
            <span>{{ dogsitter.rating.toFixed(1) }}</span>
          </div>
          <p class="experience">Опыт: {{ dogsitter.experience_years }} лет</p>
          <p class="description">{{ dogsitter.description }}</p>
        </div>
        <div v-if="isAdmin" class="admin-actions">
          <button 
            @click="toggleBlock" 
            class="block-button"
            :class="{ 'blocked': dogsitter.is_blocked }"
            :disabled="blockLoading"
          >
            {{ blockLoading ? 'Обработка...' : (dogsitter.is_blocked ? 'Разблокировать' : 'Заблокировать') }}
          </button>
        </div>
      </div>

      <div class="profile-sections">
        <div class="section reviews">
          <h2>Отзывы</h2>
          <div v-if="dogsitter.reviews && dogsitter.reviews.length > 0" class="reviews-list">
            <div v-for="review in dogsitter.reviews" :key="review.id" class="review-card">
              <div class="review-header">
                <span class="review-author">{{ review.user.first_name }} {{ review.user.last_name }}</span>
                <span class="review-rating">★ {{ review.rating.toFixed(1) }}</span>
              </div>
              <p class="review-text">{{ review.text }}</p>
              <span class="review-date">{{ formatDate(review.created_at) }}</span>
            </div>
          </div>
          <div v-else class="no-reviews">
            Пока нет отзывов
          </div>
        </div>

        <div class="section statistics">
          <h2>Статистика</h2>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ dogsitter.total_bookings || 0 }}</span>
              <span class="stat-label">Всего бронирований</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dogsitter.completed_bookings || 0 }}</span>
              <span class="stat-label">Завершено</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dogsitter.unique_clients || 0 }}</span>
              <span class="stat-label">Клиентов</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dogsitter.reviews?.length || 0 }}</span>
              <span class="stat-label">Отзывов</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { api } from '../api/config'

export default {
  name: 'DogSitterProfile',
  setup() {
    const route = useRoute()
    const store = useStore()
    const dogsitter = ref(null)
    const loading = ref(true)
    const error = ref(null)
    const blockLoading = ref(false)
    
    const isAdmin = computed(() => {
      console.log('Current user:', store.state.auth.user)
      return store.state.auth.user?.is_superuser === true
    })

    const fetchDogSitter = async () => {
      try {
        loading.value = true
        error.value = null
        const response = await api.get(`/api/dogsitters/${route.params.id}/`)
        console.log('Loaded dogsitter:', response.data)
        dogsitter.value = response.data
      } catch (err) {
        console.error('Error loading dogsitter:', err)
        error.value = 'Не удалось загрузить профиль догситтера'
      } finally {
        loading.value = false
      }
    }

    const toggleBlock = async () => {
      if (!dogsitter.value) return

      try {
        blockLoading.value = true
        const action = dogsitter.value.is_blocked ? 'unblock' : 'block'
        console.log(`Attempting to ${action} dogsitter:`, dogsitter.value)
        
        await api.post(`/api/dogsitters/${dogsitter.value.id}/${action}/`)
        dogsitter.value.is_blocked = !dogsitter.value.is_blocked
      } catch (err) {
        console.error('Error toggling block status:', err)
        error.value = 'Не удалось изменить статус блокировки'
      } finally {
        blockLoading.value = false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    onMounted(() => {
      console.log('DogSitterProfile mounted, isAdmin:', isAdmin.value)
      fetchDogSitter()
    })

    return {
      dogsitter,
      loading,
      error,
      isAdmin,
      blockLoading,
      toggleBlock,
      formatDate
    }
  }
}
</script>

<style scoped>
.dogsitter-profile {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.loading {
  text-align: center;
  padding: 40px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b983;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: #dc3545;
  text-align: center;
  padding: 20px;
  background-color: #f8d7da;
  border-radius: 4px;
  margin: 20px 0;
}

.profile-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.profile-header {
  display: flex;
  gap: 30px;
  padding: 30px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.profile-avatar {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.profile-info {
  flex: 1;
}

.profile-info h1 {
  margin: 0 0 10px;
  color: #2c3e50;
}

.rating {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;
  font-size: 1.2em;
}

.stars {
  color: #ffd700;
}

.experience {
  color: #666;
  margin: 5px 0;
}

.description {
  color: #2c3e50;
  line-height: 1.6;
}

.admin-actions {
  align-self: flex-start;
}

.block-button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background-color: #dc3545;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s;
}

.block-button:hover {
  background-color: #c82333;
}

.block-button.blocked {
  background-color: #28a745;
}

.block-button.blocked:hover {
  background-color: #218838;
}

.block-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.profile-sections {
  padding: 30px;
}

.section {
  margin-bottom: 40px;
}

.section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.reviews-list {
  display: grid;
  gap: 20px;
}

.review-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.review-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.review-author {
  font-weight: bold;
  color: #2c3e50;
}

.review-rating {
  color: #ffd700;
}

.review-text {
  color: #2c3e50;
  line-height: 1.6;
  margin: 10px 0;
}

.review-date {
  color: #6c757d;
  font-size: 0.9em;
}

.no-reviews {
  text-align: center;
  color: #6c757d;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 2em;
  font-weight: bold;
  color: #42b983;
  margin-bottom: 5px;
}

.stat-label {
  color: #6c757d;
}

@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .admin-actions {
    align-self: center;
    margin-top: 20px;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style> 