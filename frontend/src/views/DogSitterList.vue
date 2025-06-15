<template>
  <div class="dogsitter-list">
    <h1>Список догситтеров</h1>
    
    <div class="filters">
      <div class="filter-group">
        <label for="minRating">Минимальный рейтинг:</label>
        <select v-model="filters.minRating" id="minRating" class="form-control">
          <option value="">Все</option>
          <option value="4">4+ звезды</option>
          <option value="4.5">4.5+ звезды</option>
          <option value="5">Только 5 звезд</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="filters.hasReviews">
          Только с отзывами
        </label>
      </div>
      
      <div class="filter-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="filters.activeOnly">
          Только активные
        </label>
      </div>
    </div>

    <!-- Debug info -->
    <div v-if="isAdmin" class="debug-info">
      Вы вошли как администратор
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка списка догситтеров...</p>
    </div>
    
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    
    <div v-else class="dogsitters-grid">
      <div v-for="dogsitter in dogsitters" :key="dogsitter.id" class="dogsitter-card">
        <img :src="dogsitter.avatar || '/default-avatar.png'" alt="Фото догситтера" class="avatar">
        <div class="info">
          <h3>{{ dogsitter.first_name }} {{ dogsitter.last_name }}</h3>
          <div class="rating">
            <span class="stars">★</span>
            {{ dogsitter.rating.toFixed(1) }}
          </div>
          <p class="experience">Опыт: {{ dogsitter.experience_years }} лет</p>
          <p class="description">{{ dogsitter.description }}</p>
          <div v-if="isAdmin" class="admin-actions">
            <button 
              @click="showBlockModal(dogsitter)" 
              class="block-button"
              :class="{ 'blocked': dogsitter.is_blocked }"
            >
              {{ dogsitter.is_blocked ? 'Разблокировать' : 'Заблокировать' }}
            </button>
            <button 
              @click="showDeleteModal(dogsitter)"
              class="delete-button"
            >
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно подтверждения блокировки -->
    <div v-if="showBlockConfirmation" class="modal-overlay" @click="closeBlockModal">
      <div class="modal-content" @click.stop>
        <h3>{{ selectedDogsitter?.is_blocked ? 'Разблокировать догситтера?' : 'Заблокировать догситтера?' }}</h3>
        <div class="dogsitter-info" v-if="selectedDogsitter">
          <img 
            :src="selectedDogsitter.avatar || '/default-avatar.png'" 
            :alt="selectedDogsitter.first_name"
            class="modal-avatar"
          >
          <div class="modal-dogsitter-details">
            <p><strong>Имя:</strong> {{ selectedDogsitter.first_name }} {{ selectedDogsitter.last_name }}</p>
            <p><strong>Рейтинг:</strong> {{ selectedDogsitter.rating.toFixed(1) }}</p>
            <p><strong>Опыт:</strong> {{ selectedDogsitter.experience_years }} лет</p>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="confirmBlock" class="confirm-button" :disabled="blockLoading">
            {{ blockLoading ? 'Обработка...' : (selectedDogsitter?.is_blocked ? 'Разблокировать' : 'Заблокировать') }}
          </button>
          <button @click="closeBlockModal" class="cancel-button" :disabled="blockLoading">
            Отмена
          </button>
        </div>
      </div>
    </div>

    <!-- Модальное окно подтверждения удаления -->
    <div v-if="showDeleteConfirmation" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal-content" @click.stop>
        <h3>Удалить догситтера?</h3>
        <div class="dogsitter-info" v-if="selectedDogsitter">
          <img 
            :src="selectedDogsitter.avatar || '/default-avatar.png'" 
            :alt="selectedDogsitter.first_name"
            class="modal-avatar"
          >
          <div class="modal-dogsitter-details">
            <p><strong>Имя:</strong> {{ selectedDogsitter.first_name }} {{ selectedDogsitter.last_name }}</p>
            <p><strong>Рейтинг:</strong> {{ selectedDogsitter.rating.toFixed(1) }}</p>
            <p><strong>Опыт:</strong> {{ selectedDogsitter.experience_years }} лет</p>
          </div>
        </div>
        <div class="warning-message">
          Это действие нельзя отменить. Все данные догситтера будут удалены.
        </div>
        <div class="modal-actions">
          <button @click="confirmDelete" class="delete-button" :disabled="deleteLoading">
            {{ deleteLoading ? 'Удаление...' : 'Удалить' }}
          </button>
          <button @click="closeDeleteModal" class="cancel-button" :disabled="deleteLoading">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api/config'
import { useStore } from 'vuex'

export default {
  name: 'DogSitterList',
  setup() {
    const store = useStore()
    const currentUser = computed(() => store.state.auth.user)
    const isAdmin = computed(() => {
      console.log('Current user:', currentUser.value)
      return currentUser.value?.is_superuser === true
    })
    const dogsitters = ref([])
    const loading = ref(true)
    const error = ref(null)
    const showBlockConfirmation = ref(false)
    const selectedDogsitter = ref(null)
    const blockLoading = ref(false)
    const showDeleteConfirmation = ref(false)
    const deleteLoading = ref(false)

    const filters = ref({
      minRating: '',
      hasReviews: false,
      activeOnly: false
    })

    const fetchDogSitters = async () => {
      try {
        loading.value = true
        error.value = null
        
        const params = new URLSearchParams()
        if (filters.value.minRating) params.append('min_rating', filters.value.minRating)
        if (filters.value.hasReviews) params.append('has_reviews', 'true')
        if (filters.value.activeOnly) params.append('active_only', 'true')
        
        const response = await api.get('/dogsitters/', { params })
        console.log('Loaded dogsitters:', response.data)
        dogsitters.value = response.data
      } catch (err) {
        console.error('Ошибка при загрузке догситтеров:', err)
        error.value = 'Не удалось загрузить список догситтеров'
      } finally {
        loading.value = false
      }
    }

    const showBlockModal = (dogsitter) => {
      console.log('Opening block modal for dogsitter:', dogsitter)
      selectedDogsitter.value = dogsitter
      showBlockConfirmation.value = true
    }

    const closeBlockModal = () => {
      showBlockConfirmation.value = false
      selectedDogsitter.value = null
    }

    const confirmBlock = async () => {
      if (!selectedDogsitter.value) return

      try {
        blockLoading.value = true
        const action = selectedDogsitter.value.is_blocked ? 'unblock' : 'block'
        console.log(`Attempting to ${action} dogsitter:`, selectedDogsitter.value)
        
        await api.post(`/api/dogsitters/${selectedDogsitter.value.id}/${action}/`)
        
        // Обновляем состояние догситтера в списке
        const index = dogsitters.value.findIndex(d => d.id === selectedDogsitter.value.id)
        if (index !== -1) {
          dogsitters.value[index].is_blocked = !dogsitters.value[index].is_blocked
        }
        
        closeBlockModal()
      } catch (err) {
        console.error('Ошибка при блокировке/разблокировке догситтера:', err)
        error.value = 'Не удалось выполнить операцию'
      } finally {
        blockLoading.value = false
      }
    }

    const showDeleteModal = (dogsitter) => {
      console.log('Opening delete modal for dogsitter:', dogsitter)
      selectedDogsitter.value = dogsitter
      showDeleteConfirmation.value = true
    }

    const closeDeleteModal = () => {
      showDeleteConfirmation.value = false
      selectedDogsitter.value = null
    }

    const confirmDelete = async () => {
      if (!selectedDogsitter.value) return

      try {
        deleteLoading.value = true
        console.log(`Attempting to delete dogsitter:`, selectedDogsitter.value)
        
        await api.delete(`/api/dogsitters/${selectedDogsitter.value.id}/`)
        
        // Удаляем догситтера из списка
        dogsitters.value = dogsitters.value.filter(d => d.id !== selectedDogsitter.value.id)
        
        closeDeleteModal()
      } catch (err) {
        console.error('Ошибка при удалении догситтера:', err)
        error.value = 'Не удалось удалить догситтера'
      } finally {
        deleteLoading.value = false
      }
    }

    onMounted(() => {
      console.log('Component mounted, isAdmin:', isAdmin.value)
      fetchDogSitters()
    })

    return {
      dogsitters,
      loading,
      error,
      filters,
      isAdmin,
      showBlockConfirmation,
      showDeleteConfirmation,
      selectedDogsitter,
      blockLoading,
      deleteLoading,
      showBlockModal,
      closeBlockModal,
      confirmBlock,
      showDeleteModal,
      closeDeleteModal,
      confirmDelete
    }
  }
}
</script>

<style scoped>
.dogsitter-list {
  padding: 20px;
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
}

.filters {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-control {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.dogsitters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.dogsitter-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  transition: transform 0.2s, box-shadow 0.2s;
}

.dogsitter-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.avatar {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.info {
  padding: 20px;
}

.info h3 {
  margin: 0 0 10px;
  color: #2c3e50;
}

.rating {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;
}

.stars {
  color: #ffd700;
}

.experience {
  color: #666;
  margin: 5px 0;
}

.description {
  font-size: 0.9em;
  color: #666;
  margin: 10px 0;
}

.admin-actions {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.block-button {
  width: 100%;
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

.delete-button {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 8px;
  transition: background-color 0.2s;
}

.delete-button:hover {
  background-color: #c82333;
}

.delete-button:disabled {
  background-color: #e9a5ac;
  cursor: not-allowed;
}

.warning-message {
  color: #dc3545;
  margin: 16px 0;
  text-align: center;
  font-weight: bold;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
}

.modal-content h3 {
  margin: 0 0 20px;
  color: #2c3e50;
}

.dogsitter-info {
  display: flex;
  align-items: center;
  margin: 24px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.modal-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.modal-dogsitter-details {
  margin-left: 16px;
}

.modal-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.confirm-button, .cancel-button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.confirm-button {
  background-color: #dc3545;
  color: white;
}

.confirm-button:hover {
  background-color: #c82333;
}

.cancel-button {
  background-color: #6c757d;
  color: white;
}

.cancel-button:hover {
  background-color: #5a6268;
}

.confirm-button:disabled, .cancel-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .filters {
    flex-direction: column;
  }

  .dogsitter-info {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}

.debug-info {
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 10px;
  margin: 10px 0;
  border-radius: 4px;
  text-align: center;
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

.loading {
  text-align: center;
  padding: 40px;
}

.error {
  color: #dc3545;
  text-align: center;
  padding: 20px;
  background-color: #f8d7da;
  border-radius: 4px;
  margin: 20px 0;
}
</style> 