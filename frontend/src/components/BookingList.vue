<template>
  <div class="bookings-container">
    <h2>Мои бронирования</h2>
    <div v-if="loading" class="loading">
      Загрузка бронирований...
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else-if="bookings.length === 0" class="no-bookings">
      У вас пока нет бронирований
    </div>
    <div v-else class="bookings-grid">
      <div v-for="booking in bookings" :key="booking.id" class="booking-card" @click="openEditForm(booking)">
        <div class="booking-header">
          <h3>
            {{ getDogSitterName(booking) }}
          </h3>
          <span :class="['status', booking.status]">{{ getStatusText(booking.status) }}</span>
        </div>
        <div class="booking-details">
          <p><strong>Дата начала:</strong> {{ formatDate(booking.start_date) }}</p>
          <p><strong>Дата окончания:</strong> {{ formatDate(booking.end_date) }}</p>
          <p><strong>Стоимость:</strong> {{ booking.total_price || 0 }}₽</p>
        </div>
        <div class="booking-actions" v-if="booking.status === 'pending' || booking.status === 'confirmed'">
          <button @click.stop="openCancelModal(booking)" class="cancel-button" :disabled="loading">
            Отменить бронирование
          </button>
        </div>
      </div>
    </div>

    <!-- Модальное окно редактирования бронирования -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content edit-modal" @click.stop>
        <BookingEditForm
          :booking-id="selectedBooking?.id"
          @close="closeEditModal"
          @update="handleBookingUpdate"
        />
      </div>
    </div>

    <!-- Модальное окно подтверждения отмены -->
    <div v-if="showCancelModal" class="modal-overlay" @click="closeCancelModal">
      <div class="modal-content" @click.stop>
        <h3>Подтверждение отмены</h3>
        <p>Вы действительно хотите отменить бронирование?</p>
        <div class="booking-info" v-if="selectedBooking">
          <p><strong>Догситтер:</strong> {{ getDogSitterName(selectedBooking) }}</p>
          <p><strong>Дата начала:</strong> {{ formatDate(selectedBooking.start_date) }}</p>
          <p><strong>Дата окончания:</strong> {{ formatDate(selectedBooking.end_date) }}</p>
          <p><strong>Стоимость:</strong> {{ selectedBooking.total_price || 0 }}₽</p>
        </div>
        <div class="modal-actions">
          <button @click="confirmCancel" class="confirm-button" :disabled="loading">
            {{ loading ? 'Отмена...' : 'Подтвердить' }}
          </button>
          <button @click="closeCancelModal" class="cancel-modal-button" :disabled="loading">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import { api } from '../api/config'
import { useRouter } from 'vue-router'
import BookingEditForm from './BookingEditForm.vue'

export default {
  name: 'BookingList',
  components: {
    BookingEditForm
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const bookings = ref([])
    const loading = ref(true)
    const error = ref(null)
    const showCancelModal = ref(false)
    const showEditModal = ref(false)
    const selectedBooking = ref(null)

    const getDogSitterName = (booking) => {
      console.log('Обработка данных догситтера:', booking)
      
      if (!booking) {
        console.log('Бронирование отсутствует')
        return 'Догситтер не назначен'
      }

      // Проверяем структуру данных догситтера
      if (booking.dog_sitter) {
        console.log('Данные догситтера:', booking.dog_sitter)
        
        // Проверяем наличие вложенного объекта user
        if (booking.dog_sitter.user) {
          const { first_name = '', last_name = '' } = booking.dog_sitter.user
          const fullName = `${first_name} ${last_name}`.trim()
          return fullName || 'Имя догситтера не указано'
        }
        
        // Если нет user объекта, пробуем получить имя из самого объекта dog_sitter
        if (booking.dog_sitter.first_name || booking.dog_sitter.last_name) {
          const { first_name = '', last_name = '' } = booking.dog_sitter
          const fullName = `${first_name} ${last_name}`.trim()
          return fullName || 'Имя догситтера не указано'
        }
        
        return `Догситтер #${booking.dog_sitter.id}`
      }

      console.log('Догситтер не найден в данных')
      return 'Догситтер не назначен'
    }

    const getStatusText = (status) => {
      const statusMap = {
        pending: 'Ожидает подтверждения',
        confirmed: 'Подтверждено',
        completed: 'Завершено',
        cancelled: 'Отменено'
      }
      return statusMap[status] || 'Статус неизвестен'
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'Дата не указана'
      try {
        return new Date(dateString).toLocaleDateString('ru-RU', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      } catch (err) {
        console.error('Error formatting date:', err)
        return 'Некорректная дата'
      }
    }

    const openEditForm = (booking) => {
      selectedBooking.value = booking
      showEditModal.value = true
    }

    const closeEditModal = () => {
      showEditModal.value = false
      selectedBooking.value = null
    }

    const handleBookingUpdate = (updatedBooking) => {
      const index = bookings.value.findIndex(b => b.id === updatedBooking.id)
      if (index !== -1) {
        bookings.value[index] = updatedBooking
      }
    }

    const openCancelModal = (booking) => {
      selectedBooking.value = booking
      showCancelModal.value = true
    }

    const closeCancelModal = () => {
      showCancelModal.value = false
      selectedBooking.value = null
    }

    const confirmCancel = async () => {
      if (!selectedBooking.value) return

      try {
        loading.value = true
        await api.post(`/bookings/${selectedBooking.value.id}/cancel/`)
        
        // Обновляем статус бронирования локально
        const booking = bookings.value.find(b => b.id === selectedBooking.value.id)
        if (booking) {
          booking.status = 'cancelled'
        }
        
        closeCancelModal()
      } catch (err) {
        console.error('Error cancelling booking:', err)
        error.value = 'Ошибка при отмене бронирования'
      } finally {
        loading.value = false
      }
    }

    const fetchBookings = async () => {
      try {
        loading.value = true
        error.value = null
        
        // Проверяем наличие токена
        const token = store.state.auth.token
        if (!token) {
          console.log('Токен отсутствует, перенаправление на страницу входа')
          error.value = 'Необходима авторизация'
          router.push('/login')
          return
        }

        const response = await api.get('/bookings/')
        console.log('Полный ответ от сервера:', response)
        console.log('Данные бронирований:', response.data)
        
        if (response.data && Array.isArray(response.data)) {
          response.data.forEach((booking, index) => {
            console.log(`Бронирование ${index + 1}:`, booking)
            if (booking.dog_sitter) {
              console.log(`Догситтер для бронирования ${index + 1}:`, booking.dog_sitter)
            }
          })
          bookings.value = response.data
        } else {
          console.error('Неверный формат данных:', response.data)
          error.value = 'Ошибка формата данных'
          bookings.value = []
        }
      } catch (err) {
        console.error('Ошибка при загрузке бронирований:', err)
        if (err.response) {
          if (err.response.status === 401) {
            error.value = 'Необходима авторизация'
            router.push('/login')
          } else {
            error.value = `Ошибка сервера: ${err.response.status}`
          }
        } else if (err.request) {
          error.value = 'Сервер недоступен'
        } else {
          error.value = 'Ошибка при загрузке бронирований'
        }
        bookings.value = []
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchBookings()
    })

    return {
      bookings,
      loading,
      error,
      showCancelModal,
      showEditModal,
      selectedBooking,
      getStatusText,
      formatDate,
      getDogSitterName,
      openCancelModal,
      closeCancelModal,
      confirmCancel,
      openEditForm,
      closeEditModal,
      handleBookingUpdate
    }
  }
}
</script>

<style scoped>
.bookings-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.bookings-container h2 {
  color: #2c3e50;
  margin-bottom: 2rem;
  text-align: center;
}

.loading, .error, .no-bookings {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #dc3545;
}

.bookings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
}

.booking-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #eee;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.booking-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
}

.status {
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.9rem;
}

.status.pending {
  background-color: #ffeeba;
  color: #856404;
}

.status.confirmed {
  background-color: #d4edda;
  color: #155724;
}

.status.completed {
  background-color: #cce5ff;
  color: #004085;
}

.status.cancelled {
  background-color: #f8d7da;
  color: #721c24;
}

.booking-details {
  color: #666;
}

.booking-details p {
  margin: 0.5rem 0;
}

.booking-details strong {
  color: #2c3e50;
}

.booking-actions {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.cancel-button {
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 0.9rem;
  width: 100%;
}

.cancel-button:hover {
  background-color: #c82333;
}

.cancel-button:disabled {
  background-color: #e9a8ae;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.modal-content h3 {
  margin: 0 0 1rem;
  color: #2c3e50;
}

.booking-info {
  margin: 1rem 0;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.booking-info p {
  margin: 0.5rem 0;
  color: #666;
}

.booking-info strong {
  color: #2c3e50;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.confirm-button, .cancel-modal-button {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.confirm-button {
  background-color: #dc3545;
  color: white;
}

.confirm-button:hover {
  background-color: #c82333;
}

.confirm-button:disabled {
  background-color: #e9a8ae;
  cursor: not-allowed;
}

.cancel-modal-button {
  background-color: #6c757d;
  color: white;
}

.cancel-modal-button:hover {
  background-color: #5a6268;
}

.cancel-modal-button:disabled {
  background-color: #a8a8a8;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .bookings-container {
    padding: 1rem;
  }
  
  .bookings-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95%;
    padding: 1.5rem;
  }
}
</style> 