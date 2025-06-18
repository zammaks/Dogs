<template>
  <div class="dogsitter-list">
    <h1>Список догситтеров</h1>
    
    <!-- Добавляем поисковую строку -->
    <div class="search-container">
      <div class="search-input-wrapper">
        <input
          type="text"
          v-model="searchQuery"
          @input="handleSearch"
          @focus="showSuggestions = true"
          @blur="hideSuggestionsDelayed"
          placeholder="Поиск догситтера..."
          class="search-input"
        >
        <div class="search-icons">
          <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
            <path fill="currentColor" d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
          <span v-if="searchQuery" @click="clearSearch" class="clear-search">×</span>
        </div>
      </div>
      
      <!-- Выпадающий список с подсказками -->
      <div v-if="showSuggestions && filteredSuggestions.length > 0" class="search-suggestions">
        <div
          v-for="suggestion in filteredSuggestions"
          :key="suggestion.id"
          @mousedown="selectSuggestion(suggestion)"
          class="suggestion-item"
        >
          <div class="suggestion-photo">
            <img :src="getPhotoUrl(suggestion.avatar)" :alt="suggestion.first_name">
          </div>
          <div class="suggestion-info">
            <div class="suggestion-name">
              {{ suggestion.first_name }} {{ suggestion.last_name }}
            </div>
            <div class="suggestion-details">
              <span class="suggestion-rating">★ {{ suggestion.average_rating ? suggestion.average_rating.toFixed(1) : '0.0' }}</span>
              <span class="suggestion-experience">
                Опыт: {{ getExperienceString(suggestion.experience_years) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Добавляем панель фильтров -->
    <div class="filters-panel">
      <div class="filter-group">
        <label>Рейтинг:</label>
        <div class="rating-filter">
          <input 
            type="number" 
            v-model.number="filters.min_rating" 
            min="0" 
            max="5" 
            step="0.5"
            placeholder="Мин"
          >
          <span>-</span>
          <input 
            type="number" 
            v-model.number="filters.max_rating" 
            min="0" 
            max="5" 
            step="0.5"
            placeholder="Макс"
          >
        </div>
      </div>

      <div class="filter-group">
        <label>Опыт (лет):</label>
        <div class="experience-filter">
          <input 
            type="number" 
            v-model.number="filters.min_experience" 
            min="0"
            placeholder="Мин"
          >
          <span>-</span>
          <input 
            type="number" 
            v-model.number="filters.max_experience" 
            min="0"
            placeholder="Макс"
          >
        </div>
      </div>

      <div class="filter-group">
        <label>Отзывы:</label>
        <div class="reviews-filter">
          <input 
            type="number" 
            v-model.number="filters.min_reviews" 
            min="0"
            placeholder="Мин. кол-во"
          >
        </div>
      </div>

      <div class="filter-group">
        <label>
          <input 
            type="checkbox" 
            v-model="filters.has_reviews"
          >
          Только с отзывами
        </label>
      </div>

      <div class="filter-group">
        <label>
          <input 
            type="checkbox" 
            v-model="filters.is_available"
          >
          Только доступные
        </label>
      </div>

      <div class="filter-group">
        <label>Сортировать по:</label>
        <select v-model="filters.sort_by">
          <option value="">Без сортировки</option>
          <option value="rating">Рейтингу (по убыванию)</option>
          <option value="rating_asc">Рейтингу (по возрастанию)</option>
          <option value="experience">Опыту (по убыванию)</option>
          <option value="experience_asc">Опыту (по возрастанию)</option>
          <option value="reviews">Отзывам (по убыванию)</option>
          <option value="reviews_asc">Отзывам (по возрастанию)</option>
          <option value="name">Имени (А-Я)</option>
          <option value="name_desc">Имени (Я-А)</option>
        </select>
      </div>

      <button @click="resetFilters" class="reset-filters">
        Сбросить фильтры
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка списка догситтеров...</p>
    </div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="dogsitters-grid">
      <div v-for="sitter in filteredAndSortedDogsitters" :key="sitter.id" class="dogsitter-card">
        <div class="sitter-photo">
          <img 
            :src="getPhotoUrl(sitter.avatar)"
            :alt="sitter.first_name + ' ' + sitter.last_name"
          >
        </div>
        <div class="sitter-info">
          <h3>{{ sitter.first_name }} {{ sitter.last_name }}</h3>
          <div class="sitter-details">
            <p class="experience">Опыт передержки: {{ getExperienceString(sitter.experience_years) }}</p>
            <p class="age">{{ getAgeString(sitter.age) }}</p>
          </div>
          <div class="card-footer">
            <div class="rating">
              <span class="stars">
                <i v-for="n in 5" :key="n" class="star" 
                   :class="{ 'filled': n <= Math.round(sitter.average_rating || 0) }">★</i>
              </span>
              <span class="rating-value">{{ sitter.average_rating ? sitter.average_rating.toFixed(1) : '0.0' }}</span>
            </div>
            <div v-if="isAdmin" class="admin-actions">
              <button 
                @click.stop="showDeleteModal(sitter)"
                class="delete-button"
              >
                Удалить
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно подтверждения удаления -->
    <div v-if="showDeleteConfirmation" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal-content" @click.stop>
        <h3>Удалить догситтера?</h3>
        <div class="dogsitter-info" v-if="selectedDogsitter">
          <img 
            :src="getPhotoUrl(selectedDogsitter.avatar)" 
            :alt="selectedDogsitter.first_name + ' ' + selectedDogsitter.last_name"
            class="modal-avatar"
          >
          <div class="modal-dogsitter-details">
            <p><strong>Имя:</strong> {{ selectedDogsitter.first_name }} {{ selectedDogsitter.last_name }}</p>
            <p><strong>Рейтинг:</strong> {{ selectedDogsitter.average_rating ? selectedDogsitter.average_rating.toFixed(1) : '0.0' }}</p>
            <p><strong>Опыт:</strong> {{ getExperienceString(selectedDogsitter.experience_years) }}</p>
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
import axios from 'axios'
import { ref, onMounted, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { api, endpoints } from '../api/config'
import { useRouter } from 'vue-router'

export default {
  name: 'DogSitterList',
  setup() {
    const store = useStore()
    const router = useRouter()
    const dogsitters = ref([])
    const loading = ref(true)
    const error = ref(null)
    const searchQuery = ref('')
    const showSuggestions = ref(false)
    let hideTimeout = null
    const showDeleteConfirmation = ref(false)
    const deleteLoading = ref(false)
    const selectedDogsitter = ref(null)

    // Добавляем состояние для фильтров
    const filters = ref({
      min_rating: null,
      max_rating: null,
      min_experience: null,
      max_experience: null,
      min_reviews: null,
      has_reviews: false,
      is_available: false,
      sort_by: ''
    })

    // Функция для сброса фильтров
    const resetFilters = () => {
      filters.value = {
        min_rating: null,
        max_rating: null,
        min_experience: null,
        max_experience: null,
        min_reviews: null,
        has_reviews: false,
        is_available: false,
        sort_by: ''
      }
      fetchDogSitters()
    }

    const isAdmin = computed(() => {
      const user = store.state.auth.user
      const token = store.state.auth.token
      console.log('Auth state:', { user, token })
      console.log('Current user in DogSitterList:', user)
      console.log('Is superuser:', user?.is_superuser)
      return user?.is_superuser === true
    })

    const getPhotoUrl = (photoPath) => {
      if (!photoPath) return '/images/default_avatar.jpg'
      if (photoPath.startsWith('http')) return photoPath
      return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/media/${photoPath}`
    }

    const getAgeString = (age) => {
      if (!age) return 'Возраст не указан'
      const lastDigit = age % 10
      const lastTwoDigits = age % 100

      if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
        return `${age} лет`
      }

      switch (lastDigit) {
        case 1:
          return `${age} год`
        case 2:
        case 3:
        case 4:
          return `${age} года`
        default:
          return `${age} лет`
      }
    }

    const getExperienceString = (years) => {
      if (!years) return 'Опыт не указан'
      const lastDigit = years % 10
      const lastTwoDigits = years % 100

      if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
        return `${years} лет`
      }

      switch (lastDigit) {
        case 1:
          return `${years} год`
        case 2:
        case 3:
        case 4:
          return `${years} года`
        default:
          return `${years} лет`
      }
    }

    const fetchDogSitters = async () => {
      try {
        loading.value = true
        error.value = null

        // Формируем параметры запроса из фильтров
        const params = {}
        if (filters.value.min_rating !== null) params.min_rating = filters.value.min_rating
        if (filters.value.max_rating !== null) params.max_rating = filters.value.max_rating
        if (filters.value.min_experience !== null) params.min_experience = filters.value.min_experience
        if (filters.value.max_experience !== null) params.max_experience = filters.value.max_experience
        if (filters.value.min_reviews !== null) params.min_reviews = filters.value.min_reviews
        if (filters.value.has_reviews) params.has_reviews = true
        if (filters.value.is_available) params.is_available = true
        if (filters.value.sort_by) params.sort_by = filters.value.sort_by
        if (searchQuery.value) params.name = searchQuery.value

        const response = await api.get('/dogsitters/', { params })
        console.log('API Response:', response)
        console.log('Loaded dogsitters:', response.data)
        console.log('First dogsitter data:', response.data[0])
        dogsitters.value = response.data
        loading.value = false
      } catch (err) {
        error.value = 'Ошибка при загрузке списка догситтеров'
        loading.value = false
        console.error('Error fetching dogsitters:', err)
      }
    }

    // Следим за изменениями фильтров
    watch([filters, searchQuery], () => {
      fetchDogSitters()
    }, { deep: true })

    const handleSearch = () => {
      if (hideTimeout) {
        clearTimeout(hideTimeout)
      }
      showSuggestions.value = true
    }

    const hideSuggestionsDelayed = () => {
      hideTimeout = setTimeout(() => {
        showSuggestions.value = false
      }, 200)
    }

    const clearSearch = () => {
      searchQuery.value = ''
      showSuggestions.value = false
    }

    const selectSuggestion = (suggestion) => {
      searchQuery.value = `${suggestion.first_name} ${suggestion.last_name}`
      showSuggestions.value = false
    }

    const filteredSuggestions = computed(() => {
      if (!searchQuery.value) return []
      
      const query = searchQuery.value.toLowerCase()
      return dogsitters.value.filter(sitter => {
        const fullName = `${sitter.first_name} ${sitter.last_name}`.toLowerCase()
        return fullName.includes(query)
      }).slice(0, 5) // Показываем только первые 5 совпадений
    })

    const filteredAndSortedDogsitters = computed(() => {
      let filtered = dogsitters.value
      
      // Фильтрация по поисковому запросу
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(sitter => {
          const fullName = `${sitter.first_name} ${sitter.last_name}`.toLowerCase()
          return fullName.includes(query)
        })
      }

      // Сортировка
      if (!filters.value.sort_by) return filtered

      return [...filtered].sort((a, b) => {
        let comparison = 0
        
        if (filters.value.sort_by === 'rating') {
          comparison = b.rating - a.rating
        } else if (filters.value.sort_by === 'experience') {
          comparison = (b.experience_years || 0) - (a.experience_years || 0)
        } else if (filters.value.sort_by === 'reviews') {
          comparison = (b.reviews_count || 0) - (a.reviews_count || 0)
        } else if (filters.value.sort_by === 'name') {
          comparison = a.first_name.localeCompare(b.first_name)
        } else if (filters.value.sort_by === 'name_desc') {
          comparison = b.first_name.localeCompare(a.first_name)
        }

        return comparison
      })
    })

    const showDeleteModal = (sitter) => {
      console.log('Opening delete modal for dogsitter:', sitter)
      selectedDogsitter.value = sitter
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
        
        await api.delete(`/dogsitters/${selectedDogsitter.value.id}/`)
        
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
      console.log('DogSitterList mounted')
      console.log('Initial auth state:', store.state.auth)
      fetchDogSitters()
    })

    return {
      dogsitters,
      loading,
      error,
      getAgeString,
      getExperienceString,
      getPhotoUrl,
      searchQuery,
      showSuggestions,
      handleSearch,
      hideSuggestionsDelayed,
      clearSearch,
      selectSuggestion,
      filteredSuggestions,
      filteredAndSortedDogsitters,
      showDeleteConfirmation,
      selectedDogsitter,
      deleteLoading,
      showDeleteModal,
      closeDeleteModal,
      confirmDelete,
      isAdmin,
      filters,
      resetFilters
    }
  }
}
</script>

<style scoped>
.dogsitter-list {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.dogsitter-list h1 {
  margin-bottom: 30px;
  color: #2c3e50;
  text-align: center;
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
  border-radius: 8px;
  margin: 20px 0;
}

.dogsitters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 30px;
}

.dogsitter-card {
  display: flex;
  gap: 20px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.dogsitter-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.sitter-photo {
  flex: 0 0 120px;
  height: 120px;
  border-radius: 60px;
  overflow: hidden;
}

.sitter-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background-color: #f5f5f5;
}

.sitter-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sitter-info h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.4em;
  font-weight: 600;
}

.sitter-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #666;
  font-size: 1em;
}

.experience {
  color: #2c3e50;
  font-weight: 500;
}

.rating {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stars {
  color: #ffd700;
  letter-spacing: 2px;
}

.star {
  color: #ddd;
}

.star.filled {
  color: #ffd700;
}

.rating-value {
  color: #666;
  font-weight: 500;
}

.card-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sort-panel {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.sort-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1em;
  color: #2c3e50;
  background-color: white;
  cursor: pointer;
}

.sort-direction {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  font-size: 1.2em;
  color: #2c3e50;
  transition: all 0.2s;
}

.sort-direction:hover {
  background-color: #f1f1f1;
}

.search-container {
  position: relative;
  margin-bottom: 20px;
  width: 100%;
  max-width: 600px;
  margin: 0 auto 30px;
}

.search-input-wrapper {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  padding: 12px 45px 12px 15px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1.1em;
  transition: all 0.3s;
  background: white;
}

.search-input:focus {
  border-color: #42b983;
  outline: none;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.1);
}

.search-icons {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-icon {
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
  order: 2;
}

.search-icon:hover {
  color: #42b983;
}

.clear-search {
  cursor: pointer;
  color: #666;
  font-size: 1.5em;
  line-height: 1;
  padding: 5px;
  order: 1;
}

.clear-search:hover {
  color: #333;
}

.search-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  margin-top: 5px;
  z-index: 1000;
  max-height: 400px;
  overflow-y: auto;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  gap: 15px;
}

.suggestion-item:hover {
  background-color: #f5f5f5;
}

.suggestion-photo {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  overflow: hidden;
  flex-shrink: 0;
}

.suggestion-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.suggestion-info {
  flex: 1;
}

.suggestion-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
}

.suggestion-details {
  display: flex;
  gap: 15px;
  font-size: 0.9em;
  color: #666;
}

.suggestion-rating {
  color: #ffd700;
}

.upcoming-bookings,
.bookings-grid,
.booking-card,
.booking-sitter-photo,
.booking-info,
.booking-date,
.booking-status,
.view-all-bookings,
.no-bookings {
  display: none;
}

@media (max-width: 768px) {
  .dogsitter-list {
    padding: 20px;
  }

  .dogsitters-grid {
    grid-template-columns: 1fr;
  }

  .dogsitter-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .sitter-photo {
    flex: 0 0 150px;
    height: 150px;
    border-radius: 75px;
  }

  .card-footer {
    width: 100%;
  }

  .sort-panel {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .search-container {
    padding: 0 20px;
  }
  
  .search-suggestions {
    margin-top: 10px;
  }
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

.modal-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
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

.modal-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.modal-dogsitter-details {
  margin-left: 16px;
}

.dogsitter-info {
  display: flex;
  align-items: center;
  margin: 24px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.admin-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.filters-panel {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-weight: 500;
  color: #2c3e50;
}

.rating-filter,
.experience-filter,
.reviews-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rating-filter input,
.experience-filter input,
.reviews-filter input {
  width: 80px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.filter-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  min-width: 200px;
}

.reset-filters {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.reset-filters:hover {
  background: #c0392b;
}
</style> 