<template>
  <div class="booking-edit-form" @click.self="$emit('close')">
    <div v-if="loading" class="loading">
      Загрузка данных...
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <form v-else @submit.prevent="handleSubmit" class="form-container">
      <h2>Редактирование бронирования</h2>
      
      <div class="form-group">
        <label>Догситтер</label>
        <div class="info-text">{{ getDogSitterName(booking) }}</div>
      </div>

      <div class="form-group">
        <label for="startDate">Дата начала</label>
        <input
          type="date"
          id="startDate"
          v-model="formData.start_date"
          class="form-control"
          :min="minDate"
          required
        >
      </div>

      <div class="form-group">
        <label for="endDate">Дата окончания</label>
        <input
          type="date"
          id="endDate"
          v-model="formData.end_date"
          class="form-control"
          :min="formData.start_date"
          required
        >
      </div>

      <div class="form-group">
        <label>Животные</label>
        <div class="animals-list">
          <div v-for="animal in booking.animals" :key="animal.id" class="animal-item">
            <span>{{ animal.name }} ({{ animal.type }})</span>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label>Услуги</label>
        <div class="services-list">
          <div v-for="service in availableServices" :key="service.id" class="service-item">
            <label class="checkbox-label">
              <input
                type="checkbox"
                v-model="formData.services"
                :value="service.id"
              >
              {{ service.name }} - {{ service.price }}₽
            </label>
          </div>
        </div>
      </div>

      <div class="form-group total-price">
        <label>Общая стоимость:</label>
        <div class="price">{{ calculateTotalPrice() }}₽</div>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Сохранение...' : 'Сохранить изменения' }}
        </button>
        <button type="button" class="btn-secondary" @click="$emit('close')">
          Отмена
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/config'

export default {
  name: 'BookingEditForm',
  props: {
    bookingId: {
      type: Number,
      required: true
    }
  },
  emits: ['close', 'update'],
  setup(props, { emit }) {
    const booking = ref(null)
    const loading = ref(true)
    const error = ref(null)
    const availableServices = ref([])

    const formData = ref({
      start_date: '',
      end_date: '',
      services: []
    })

    const minDate = computed(() => {
      const today = new Date()
      return today.toISOString().split('T')[0]
    })

    const getDogSitterName = (booking) => {
      if (!booking || !booking.dog_sitter) return 'Догситтер не назначен'
      
      const dogSitter = booking.dog_sitter
      if (dogSitter.user) {
        return `${dogSitter.user.first_name} ${dogSitter.user.last_name}`.trim()
      }
      return `Догситтер #${dogSitter.id}`
    }

    const calculateTotalPrice = () => {
      if (!booking.value || !formData.value.start_date || !formData.value.end_date) return 0

      const days = Math.ceil(
        (new Date(formData.value.end_date) - new Date(formData.value.start_date)) / 
        (1000 * 60 * 60 * 24)
      )

      if (days <= 0) return 0

      const selectedServices = availableServices.value.filter(
        service => formData.value.services.includes(service.id)
      )
      
      const servicesPrice = selectedServices.reduce(
        (sum, service) => sum + (service?.price || 0), 
        0
      )

      const animalsPrice = (booking.value.animals || []).reduce((sum, animal) => {
        const sizePrices = {
          'Маленький': 500,
          'Средний': 700,
          'Крупный': 1000
        }
        return sum + (sizePrices[animal?.size] || 500)
      }, 0)

      return (servicesPrice + animalsPrice) * days
    }

    const fetchBookingData = async () => {
      try {
        loading.value = true
        error.value = null
        
        const [bookingResponse, servicesResponse] = await Promise.all([
          api.get(`/bookings/${props.bookingId}/`),
          api.get('/services/')
        ])

        booking.value = bookingResponse.data
        availableServices.value = servicesResponse.data

        formData.value = {
          start_date: booking.value?.start_date || '',
          end_date: booking.value?.end_date || '',
          services: booking.value?.services?.map(service => service.id) || []
        }
      } catch (err) {
        console.error('Ошибка при загрузке данных:', err)
        error.value = 'Не удалось загрузить данные бронирования'
      } finally {
        loading.value = false
      }
    }

    const handleSubmit = async () => {
      try {
        loading.value = true
        error.value = null

        const response = await api.patch(`/bookings/${props.bookingId}/`, {
          start_date: formData.value.start_date,
          end_date: formData.value.end_date,
          services: formData.value.services
        })

        emit('update', response.data)
        emit('close')
      } catch (err) {
        console.error('Ошибка при сохранении:', err)
        error.value = err.response?.data?.error || 'Не удалось сохранить изменения'
        loading.value = false
      }
    }

    onMounted(() => {
      fetchBookingData()
    })

    return {
      booking,
      loading,
      error,
      formData,
      minDate,
      availableServices,
      getDogSitterName,
      calculateTotalPrice,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.booking-edit-form {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  overflow-y: auto;
  padding: 20px;
}

.form-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
}

@media (max-width: 768px) {
  .booking-edit-form {
    padding: 10px;
  }

  .form-container {
    max-height: 95vh;
    padding: 15px;
    border-radius: 4px;
  }
}

/* Добавляем стили для скроллбара в форме */
.form-container::-webkit-scrollbar {
  width: 8px;
}

.form-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.form-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.form-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

h2 {
  margin-bottom: 24px;
  color: #2c3e50;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #2c3e50;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .form-control {
    font-size: 14px;
    padding: 10px;
  }

  .animal-item,
  .service-item {
    margin-bottom: 6px;
    padding: 6px;
  }

  .checkbox-label {
    font-size: 14px;
  }
}

.info-text {
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  color: #495057;
}

.animals-list,
.services-list {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 12px;
}

.animal-item,
.service-item {
  margin-bottom: 8px;
  padding: 8px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.total-price {
  background: #e9ecef;
  padding: 15px;
  border-radius: 4px;
  margin-top: 20px;
}

.price {
  font-size: 1.2em;
  font-weight: 600;
  color: #2c3e50;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
    gap: 8px;
  }

  button {
    width: 100%;
    padding: 12px;
    font-size: 14px;
  }

  .total-price {
    padding: 12px;
    margin-top: 16px;
  }

  .price {
    font-size: 1.1em;
  }
}

button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #42b983;
  color: white;
}

.btn-primary:hover {
  background-color: #3aa876;
}

.btn-primary:disabled {
  background-color: #95d5b7;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6c757d;
}

.error {
  color: #dc3545;
  padding: 12px;
  background-color: #f8d7da;
  border-radius: 4px;
  margin-bottom: 20px;
}
</style> 