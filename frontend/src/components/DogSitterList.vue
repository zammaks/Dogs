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
              <span class="suggestion-rating">★ {{ suggestion.rating.toFixed(1) }}</span>
              <span class="suggestion-experience">
                Опыт: {{ getExperienceString(suggestion.experience_years) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Добавляем панель сортировки -->
    <div class="sort-panel">
      <label for="sortBy">Сортировать по:</label>
      <select v-model="sortBy" id="sortBy" class="sort-select">
        <option value="">Без сортировки</option>
        <option value="rating">Рейтингу</option>
        <option value="experience">Опыту</option>
      </select>
      <button 
        @click="toggleSortDirection" 
        class="sort-direction"
        :title="sortDirection === 'asc' ? 'По возрастанию' : 'По убыванию'"
      >
        {{ sortDirection === 'asc' ? '↑' : '↓' }}
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
                   :class="{ 'filled': n <= Math.round(sitter.rating) }">★</i>
              </span>
              <span class="rating-value">{{ sitter.rating.toFixed(1) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted, computed } from 'vue'
import { useStore } from 'vuex'
import { endpoints } from '../api/config'
import { useRouter } from 'vue-router'

export default {
  name: 'DogSitterList',
  setup() {
    const store = useStore()
    const router = useRouter()
    const dogsitters = ref([])
    const loading = ref(true)
    const error = ref(null)
    const sortBy = ref('')
    const sortDirection = ref('desc')
    const searchQuery = ref('')
    const showSuggestions = ref(false)
    let hideTimeout = null

    const getPhotoUrl = (photoPath) => {
      if (!photoPath) return '/images/default_avatar.jpg'
      if (photoPath.startsWith('http')) return photoPath
      return `http://localhost:8000/media/${photoPath}`
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
        const token = store.state.auth.token
        const response = await axios.get(endpoints.dogsitters, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        dogsitters.value = response.data
        loading.value = false
      } catch (err) {
        error.value = 'Ошибка при загрузке списка догситтеров'
        loading.value = false
        console.error('Error fetching dogsitters:', err)
      }
    }

    const toggleSortDirection = () => {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    }

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
      if (!sortBy.value) return filtered

      return [...filtered].sort((a, b) => {
        let comparison = 0
        
        if (sortBy.value === 'rating') {
          comparison = b.rating - a.rating
        } else if (sortBy.value === 'experience') {
          comparison = (b.experience_years || 0) - (a.experience_years || 0)
        }

        return sortDirection.value === 'asc' ? -comparison : comparison
      })
    })

    onMounted(() => {
      fetchDogSitters()
    })

    return {
      dogsitters,
      loading,
      error,
      getAgeString,
      getExperienceString,
      getPhotoUrl,
      sortBy,
      sortDirection,
      toggleSortDirection,
      searchQuery,
      showSuggestions,
      handleSearch,
      hideSuggestionsDelayed,
      clearSearch,
      selectSuggestion,
      filteredSuggestions,
      filteredAndSortedDogsitters
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
</style> 