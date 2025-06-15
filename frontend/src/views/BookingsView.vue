<template>
  <div class="bookings-view">
    <h1>{{ isAdmin ? 'Все бронирования' : 'Мои бронирования' }}</h1>

    <div v-if="isAdmin" class="admin-view">
      <div v-for="user in uniqueUsers" :key="user.id" class="user-section">
        <div class="user-info-header">
          <div class="user-main-info">
            <img 
              :src="user.avatar_url || '/default-avatar.png'" 
              :alt="user.first_name"
              class="user-avatar"
            >
            <div class="user-details">
              <h2>{{ user.first_name }} {{ user.last_name }}</h2>
              <p class="user-email">{{ user.email }}</p>
            </div>
          </div>
          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-value">{{ getUserBookings(user.id).length }}</span>
              <span class="stat-label">Бронирований</span>
            </div>
          </div>
        </div>

        <div class="bookings-container">
          <div class="bookings-header">
            <h3>Бронирования пользователя</h3>
            <button class="toggle-btn" @click="toggleUserBookings(user.id)">
              {{ openUsers.includes(user.id) ? 'Свернуть' : 'Развернуть' }}
              <span class="dropdown-arrow" :class="{ 'open': openUsers.includes(user.id) }">▼</span>
            </button>
          </div>
          
          <div v-if="openUsers.includes(user.id)" class="bookings-list">
            <div v-for="booking in getUserBookings(user.id)" :key="booking.id" class="booking-card">
              <div class="booking-header">
                <h3>Бронирование #{{ booking.id }}</h3>
                <span :class="['status-badge', booking.status]">{{ getStatusText(booking.status) }}</span>
              </div>
              <div class="booking-details">
                <p><strong>Догситтер:</strong> {{ booking.dog_sitter.first_name }} {{ booking.dog_sitter.last_name }}</p>
                <p><strong>Даты:</strong> {{ formatDate(booking.start_date) }} - {{ formatDate(booking.end_date) }}</p>
                <p><strong>Животные:</strong></p>
                <ul>
                  <li v-for="animal in booking.animals" :key="animal.id">
                    {{ animal.name }} ({{ getAnimalType(animal.type) }})
                  </li>
                </ul>
                <p><strong>Стоимость:</strong> {{ booking.total_price }} ₽</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="user-view">
      <div v-for="booking in bookings" :key="booking.id" class="booking-card">
        <div class="booking-header">
          <h3>Бронирование #{{ booking.id }}</h3>
          <span :class="['status-badge', booking.status]">{{ getStatusText(booking.status) }}</span>
        </div>
        <div class="booking-details">
          <p><strong>Догситтер:</strong> {{ booking.dog_sitter.first_name }} {{ booking.dog_sitter.last_name }}</p>
          <p><strong>Даты:</strong> {{ formatDate(booking.start_date) }} - {{ formatDate(booking.end_date) }}</p>
          <p><strong>Животные:</strong></p>
          <ul>
            <li v-for="animal in booking.animals" :key="animal.id">
              {{ animal.name }} ({{ getAnimalType(animal.type) }})
            </li>
          </ul>
          <p><strong>Стоимость:</strong> {{ booking.total_price }} ₽</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import axios from 'axios'

export default {
  name: 'BookingsView',
  
  setup() {
    const store = useStore()
    const bookings = ref([])
    const openUsers = ref([])
    const isAdmin = computed(() => store.state.auth.user?.is_superuser)
    
    const uniqueUsers = computed(() => {
      const users = bookings.value.map(booking => booking.user)
      return [...new Map(users.map(user => [user.id, user])).values()]
    })
    
    const getUserBookings = (userId) => {
      return bookings.value.filter(booking => booking.user.id === userId)
    }
    
    const toggleUserBookings = (userId) => {
      const index = openUsers.value.indexOf(userId)
      if (index === -1) {
        openUsers.value.push(userId)
      } else {
        openUsers.value.splice(index, 1)
      }
    }
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('ru-RU')
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
    
    const getAnimalType = (type) => {
      const typeMap = {
        'dog': 'Собака',
        'cat': 'Кошка',
        'other': 'Другое'
      }
      return typeMap[type] || type
    }
    
    const fetchBookings = async () => {
      try {
        const response = await axios.get('/api/bookings/')
        bookings.value = response.data
      } catch (error) {
        console.error('Ошибка при загрузке бронирований:', error)
      }
    }
    
    onMounted(fetchBookings)
    
    return {
      bookings,
      isAdmin,
      uniqueUsers,
      openUsers,
      getUserBookings,
      toggleUserBookings,
      formatDate,
      getStatusText,
      getAnimalType
    }
  }
}
</script>

<style scoped>
.bookings-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.admin-view {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.user-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.user-info-header {
  background: #f8f9fa;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e9ecef;
}

.user-main-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-details {
  text-align: left;
}

.user-details h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.user-email {
  margin: 0.25rem 0 0;
  color: #6c757d;
  font-size: 0.9rem;
}

.user-stats {
  display: flex;
  gap: 2rem;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: #42b983;
}

.stat-label {
  font-size: 0.85rem;
  color: #6c757d;
}

.bookings-container {
  padding: 1.5rem;
}

.bookings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.bookings-header h3 {
  margin: 0;
  color: #2c3e50;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: #f8f9fa;
}

.dropdown-arrow {
  font-size: 0.8rem;
  transition: transform 0.2s;
}

.dropdown-arrow.open {
  transform: rotate(180deg);
}

.bookings-list {
  display: grid;
  gap: 1rem;
  margin-top: 1rem;
}

.booking-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1.25rem;
  background: white;
  transition: transform 0.2s, box-shadow 0.2s;
}

.booking-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.status-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge.pending {
  background-color: #fff3cd;
  color: #856404;
}

.status-badge.confirmed {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.completed {
  background-color: #cce5ff;
  color: #004085;
}

.status-badge.cancelled {
  background-color: #f8d7da;
  color: #721c24;
}

@media (max-width: 768px) {
  .user-info-header {
    flex-direction: column;
    gap: 1rem;
  }

  .user-stats {
    width: 100%;
    justify-content: center;
  }
}
</style> 