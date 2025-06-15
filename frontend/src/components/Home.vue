<template>
  <div class="home-container">
    <div class="welcome-section">
      <h1 class="welcome-message" v-if="currentUser">
        Привет, {{ currentUser.first_name }}!
        <span v-if="currentUser.is_superuser" class="admin-badge">АДМИНИСТРАТОР</span>
      </h1>
      <p class="welcome-subtitle">Добро пожаловать в систему поиска догситтеров</p>
    </div>

    <div class="statistics-section" v-if="statistics">
      <h2 class="statistics-title">Наши достижения:</h2>
      <div class="statistics-grid">
        <div class="stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-value">{{ statistics.completed_bookings }}</div>
          <div class="stat-label">Успешных передержек</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">👥</div>
          <div class="stat-value">{{ statistics.dogsitters_count }}</div>
          <div class="stat-label">Догситтеров</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">⭐</div>
          <div class="stat-value">{{ statistics.avg_rating }}/5</div>
          <div class="stat-label">Средняя оценка догситтеров</div>
        </div>
      </div>
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

    <div class="upcoming-bookings" v-if="currentUser">
      <h2>Ближайшие бронирования</h2>
      
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Загрузка бронирований...</p>
      </div>
      
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      
      <div v-else-if="upcomingBookings.length === 0" class="no-bookings">
        <p>У вас пока нет предстоящих бронирований</p>
      </div>
      
      <div v-else class="bookings-grid">
        <div v-for="booking in upcomingBookings" :key="booking.id" class="booking-card">
          <div class="booking-header">
            <h3>{{ getDogSitterName(booking) }}</h3>
            <span :class="['status', booking.status]">{{ getStatusText(booking.status) }}</span>
          </div>
          
          <div class="booking-details">
            <p><strong>Дата:</strong> {{ formatDate(booking.start_date) }}</p>
            <p><strong>Животные:</strong> {{ getAnimalsText(booking.animals) }}</p>
            <p><strong>Услуги:</strong> {{ getServicesText(booking.services) }}</p>
            <p class="booking-price"><strong>Стоимость:</strong> {{ formatPrice(booking.total_price) }} ₽</p>
          </div>
        </div>
      </div>
      
      <button v-if="upcomingBookings.length > 0" class="view-all-btn" @click="navigateTo('Bookings')">
        Посмотреть все бронирования
      </button>
    </div>

    <div class="popular-sitters" v-if="currentUser">
      <h2>Популярные догситтеры</h2>
      
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
        
        <div v-if="showSuggestions && filteredSuggestions.length > 0" class="search-suggestions">
          <div
            v-for="suggestion in filteredSuggestions"
            :key="suggestion.id"
            @mousedown="selectSuggestion(suggestion)"
            class="suggestion-item"
          >
            <div class="suggestion-photo">
              <img :src="getAvatarUrl(suggestion.avatar)" :alt="getSitterFullName(suggestion)">
            </div>
            <div class="suggestion-info">
              <div class="suggestion-name">
                {{ getSitterFullName(suggestion) }}
              </div>
              <div class="suggestion-details">
                <span class="suggestion-rating">★ {{ formatRating(suggestion.rating) }}</span>
                <span class="suggestion-experience">
                  Опыт: {{ getYearsText(suggestion.experience_years) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="loadingSitters" class="loading">
        <div class="spinner"></div>
        <p>Загрузка догситтеров...</p>
      </div>
      
      <div v-else-if="sitterError" class="error">
        {{ sitterError }}
      </div>
      
      <div v-else-if="popularSitters.length === 0" class="no-sitters">
        <p>Пока нет доступных догситтеров</p>
      </div>
      
      <div v-else class="sitters-grid">
        <div v-for="sitter in popularSitters" :key="sitter.id" class="sitter-card" @click="viewSitterProfile(sitter.id)">
          <div class="sitter-avatar">
            <img :src="getAvatarUrl(sitter.avatar)" :alt="getSitterFullName(sitter)">
          </div>
          <div class="sitter-info">
            <h3>{{ getSitterFullName(sitter) }}</h3>
            <div class="rating">
              <span class="stars">★</span>
              <span>{{ formatRating(sitter.rating) }}</span>
            </div>
            <p class="experience" v-if="sitter.experience_years">
              <span class="experience-icon">🎓</span>
              Опыт: {{ sitter.experience_years }} {{ getYearsText(sitter.experience_years) }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { api, endpoints, DEFAULT_AVATAR } from '../api/config'
import _ from 'lodash'
import { clickOutside } from '../directives/clickOutside'

export default {
  name: 'Home',
  directives: {
    clickOutside
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const currentUser = computed(() => store.state.auth.user)
    const upcomingBookings = ref([])
    const loading = ref(false)
    const error = ref(null)
    const popularSitters = ref([])
    const loadingSitters = ref(false)
    const sitterError = ref(null)
    const searchQuery = ref('')
    const showSuggestions = ref(false)
    const statistics = ref(null)
    let hideTimeout = null

    const getAvatarUrl = (avatar) => {
      if (!avatar) return DEFAULT_AVATAR
      if (avatar.startsWith('http')) return avatar
      return `${import.meta.env.VITE_API_URL}${avatar}`
    }

    const fetchUpcomingBookings = async () => {
      if (!store.state.auth.token) return

      try {
        loading.value = true
        error.value = null
        const response = await api.get('/bookings/')
        
        // Добавляем отладочный вывод
        console.log('Полученные бронирования:', response.data)
        
        // Фильтруем и сортируем бронирования
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        
        const sortedBookings = response.data
          .filter(booking => {
            const startDate = new Date(booking.start_date)
            startDate.setHours(0, 0, 0, 0)
            return startDate >= today
          })
          .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))
          .slice(0, 3)

        upcomingBookings.value = sortedBookings
      } catch (err) {
        console.error('Ошибка при получении бронирований:', err)
        error.value = 'Не удалось загрузить бронирования'
      } finally {
        loading.value = false
      }
    }

    const fetchPopularSitters = async () => {
      if (!store.state.auth.token) return

      try {
        loadingSitters.value = true
        sitterError.value = null
        const response = await api.get('dogsitters/', {
          params: {
            ordering: '-rating',
            limit: 3
          }
        })
        console.log('Получены догситтеры:', response.data)
        popularSitters.value = response.data || []
      } catch (err) {
        console.error('Ошибка при получении популярных догситтеров:', err)
        sitterError.value = 'Не удалось загрузить список догситтеров'
      } finally {
        loadingSitters.value = false
      }
    }

    const fetchStatistics = async () => {
      try {
        const response = await api.get('/statistics/')
        statistics.value = response.data
      } catch (err) {
        console.error('Ошибка при получении статистики:', err)
      }
    }

    const getDogSitterName = (booking) => {
      if (!booking || !booking.dog_sitter) return 'Догситтер не указан'
      const dogSitter = booking.dog_sitter
      
      if (!dogSitter.first_name) return 'Догситтер не указан'
      
      const firstName = dogSitter.first_name || ''
      const lastName = dogSitter.last_name || ''
      
      return `${firstName} ${lastName}`.trim() || 'Догситтер не указан'
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      try {
        const options = { day: 'numeric', month: 'long', year: 'numeric' }
        return new Date(dateString).toLocaleDateString('ru-RU', options)
      } catch (e) {
        console.error('Ошибка форматирования даты:', e)
        return dateString
      }
    }

    const formatPrice = (price) => {
      if (!price) return '0'
      try {
        return Number(price).toLocaleString('ru-RU')
      } catch (e) {
        console.error('Ошибка форматирования цены:', e)
        return price
      }
    }

    const getStatusText = (status) => {
      const statusMap = {
        'pending': 'Ожидает подтверждения',
        'confirmed': 'Подтверждено',
        'completed': 'Завершено',
        'cancelled': 'Отменено'
      }
      return statusMap[status] || status
    }

    const getServicesText = (services) => {
      if (!services || !Array.isArray(services) || services.length === 0) return 'Нет услуг'
      return services.map(service => service.name).join(', ')
    }

    const getAnimalsText = (animals) => {
      if (!animals || !Array.isArray(animals) || animals.length === 0) return 'Нет животных'
      return animals.map(animal => animal.name).join(', ')
    }

    const getSitterFullName = (sitter) => {
      if (!sitter) return 'Имя не указано'
      return `${sitter.first_name || ''} ${sitter.last_name || ''}`.trim() || 'Имя не указано'
    }

    const formatRating = (rating) => {
      return rating ? rating.toFixed(1) : '0.0'
    }

    const viewSitterProfile = (sitterId) => {
      router.push({ name: 'DogSitterProfile', params: { id: sitterId.toString() } })
    }

    const navigateTo = (routeName) => {
      router.push({ name: routeName })
    }

    const getYearsText = (years) => {
      if (!years) return 'лет'
      
      const lastDigit = years % 10
      const lastTwoDigits = years % 100
      
      if (lastTwoDigits >= 11 && lastTwoDigits <= 14) return 'лет'
      if (lastDigit === 1) return 'год'
      if (lastDigit >= 2 && lastDigit <= 4) return 'года'
      return 'лет'
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
      router.push({ name: 'DogSitterProfile', params: { id: suggestion.id } })
      searchQuery.value = ''
      showSuggestions.value = false
    }

    const filteredSuggestions = computed(() => {
      if (!searchQuery.value) return []
      
      const query = searchQuery.value.toLowerCase()
      return popularSitters.value.filter(sitter => {
        const fullName = getSitterFullName(sitter).toLowerCase()
        return fullName.includes(query)
      }).slice(0, 5) // Показываем только первые 5 совпадений
    })

    const getStarWidth = (rating, position) => {
      const difference = rating - (position - 1)
      if (difference >= 1) return '100%'
      if (difference > 0) return `${difference * 100}%`
      return '0%'
    }

    onMounted(() => {
      if (currentUser.value) {
        fetchUpcomingBookings()
        fetchPopularSitters()
        fetchStatistics()
      }
    })

    return {
      currentUser,
      navigateTo,
      upcomingBookings,
      loading,
      error,
      formatDate,
      formatPrice,
      getStatusText,
      getServicesText,
      getAnimalsText,
      getDogSitterName,
      popularSitters,
      loadingSitters,
      sitterError,
      getSitterFullName,
      formatRating,
      viewSitterProfile,
      getYearsText,
      getAvatarUrl,
      searchQuery,
      showSuggestions,
      handleSearch,
      hideSuggestionsDelayed,
      clearSearch,
      selectSuggestion,
      filteredSuggestions,
      statistics,
      getStarWidth,
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
  font-size: 3.5rem;
  color: #2c3e50;
  margin-bottom: 1.5rem;
  font-weight: bold;
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
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 250px;
}

.nav-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  transition: transform 0.3s ease;
}

.nav-card:hover .card-icon {
  transform: scale(1.1);
}

.nav-card h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.nav-card p {
  color: #666;
  font-size: 1.1rem;
  line-height: 1.4;
}

.popular-sitters {
  margin-top: 3rem;
}

.popular-sitters h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  text-align: center;
}

.sitters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.sitter-card {
  background: white;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sitter-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.sitter-avatar {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.sitter-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.sitter-info {
  flex-grow: 1;
}

.sitter-info h3 {
  margin: 0 0 0.5rem;
  color: #2c3e50;
  font-size: 1.2rem;
}

.rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.stars {
  color: #ffd700;
}

.experience {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  margin: 0.5rem 0;
  font-size: 0.9rem;
}

.experience-icon {
  font-size: 1.1rem;
}

.reviews-count {
  color: #666;
  font-size: 0.9rem;
}

.sitter-location {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  margin: 0.5rem 0;
}

.location-icon {
  font-size: 1.1rem;
}

.price-range {
  color: #42b983;
  font-weight: 600;
  margin: 0.5rem 0 0;
}

.no-sitters {
  text-align: center;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 8px;
  color: #666;
}

.upcoming-bookings {
  margin-top: 3rem;
}

.upcoming-bookings h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  text-align: center;
}

.bookings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.booking-card {
  background: white;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.booking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.booking-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.2rem;
}

.status {
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.9rem;
}

.status.pending {
  background-color: #fff3e0;
  color: #ef6c00;
}

.status.confirmed {
  background-color: #e3f2fd;
  color: #1976d2;
}

.status.completed {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status.cancelled {
  background-color: #ffebee;
  color: #c62828;
}

.booking-details {
  margin: 0.5rem 0;
  color: #666;
}

.booking-details strong {
  color: #2c3e50;
}

.booking-price {
  margin-top: 1rem !important;
  padding-top: 1rem;
  border-top: 1px solid #eee;
  color: #42b983 !important;
  font-size: 1.1rem;
}

.view-all-btn {
  display: block;
  margin: 0 auto;
  padding: 0.8rem 2rem;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.view-all-btn:hover {
  background: #3aa876;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b983;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: #dc3545;
  text-align: center;
  padding: 1rem;
  background-color: #f8d7da;
  border-radius: 8px;
  margin: 1rem 0;
}

.no-bookings {
  text-align: center;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 8px;
  color: #666;
}

.sitter-description {
  color: #666;
  margin: 0.5rem 0;
  font-size: 0.9rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
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

  .bookings-grid {
    grid-template-columns: 1fr;
  }

  .sitters-grid {
    grid-template-columns: 1fr;
  }

  .nav-card {
    min-height: 200px;
    padding: 1.5rem;
  }

  .card-icon {
    font-size: 3rem;
  }

  .stat-icon {
    font-size: 1rem ;
  }

  .navbar-brand {
    font-size: 1.5rem;
  }

  .logo-text {
    font-size: 1.5rem;
  }
}

.search-container {
  max-width: 600px;
  margin: 2rem auto;
  position: relative;
}

.search-input-wrapper {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  padding: 1rem 2.5rem 1rem 1rem;
  border: 2px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.1);
}

.search-icons {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.search-icon {
  color: #666;
}

.clear-search {
  cursor: pointer;
  font-size: 1.5rem;
  color: #666;
  line-height: 1;
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-top: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
  z-index: 1000;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.suggestion-item:hover {
  background-color: #f8f9fa;
}

.suggestion-photo {
  width: 40px;
  height: 40px;
  margin-right: 1rem;
  flex-shrink: 0;
}

.suggestion-photo img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.suggestion-info {
  flex-grow: 1;
}

.suggestion-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.suggestion-details {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #666;
  font-size: 0.9rem;
}

.suggestion-rating {
  color: #ffd700;
}

.suggestion-experience {
  color: #666;
}

.statistics-section {
  margin: 2rem auto;
  max-width: 1200px;
  padding: 0 1rem;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-icon {
  font-size: rem;
  margin-bottom: 1.5rem;
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #42b983;
  margin-bottom: 0.5rem;
  text-align: center;
}

.stat-label {
  color: #666;
  font-size: 1.1rem;
}

.statistics-title {
  text-align: center;
  color: #2c3e50;
  font-size: 2rem;
  margin-bottom: 2rem;
  font-weight: bold;
}

.rating-stars {
  font-size: 1.5rem;
  margin-top: 0.5rem;
  min-height: 1.5rem;
  display: flex;
  justify-content: center;
  gap: 4px;
}

.star-container {
  position: relative;
  display: inline-block;
}

.star {
  position: absolute;
  top: 0;
  left: 0;
  overflow: hidden;
}

.star.empty {
  color: #ddd;
}

.star.filled {
  color: #ffd700;
  overflow: hidden;
  position: absolute;
  top: 0;
  left: 0;
  white-space: nowrap;
}

/* Стили для логотипа */
.navbar-brand {
  display: flex;
  align-items: center;
  text-decoration: none;
  font-size: 2rem;
  font-weight: bold;
  color: var(--text-color);
  transition: transform 0.3s ease;
}

.navbar-brand:hover {
  transform: scale(1.05);
}

.logo-text {
  font-size: 2rem;
  font-weight: bold;
  background: linear-gradient(45deg, #42b983, #2c3e50);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  padding: 0.5rem;
}

.admin-badge {
  display: inline-block;
  background-color: #ff4444;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  margin-left: 10px;
  font-weight: bold;
  text-transform: uppercase;
}
</style> 