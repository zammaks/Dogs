<template>
  <div class="booking-create-form">
    <div v-if="loading" class="loading">
      Загрузка...
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <form v-else @submit.prevent="handleSubmit" class="form-container">
      <h2>Новое бронирование</h2>
      
      <div class="form-group">
        <label>Догситтер</label>
        <div class="info-text">{{ getDogSitterName() }}</div>
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
        <label>Выберите животных</label>
        <div class="animals-list">
          <div v-if="userAnimals.length === 0" class="no-animals">
            У вас пока нет добавленных животных
          </div>
          <div v-else v-for="animal in userAnimals" :key="animal.id" class="animal-item">
            <label class="checkbox-label">
              <input
                type="checkbox"
                v-model="formData.animals"
                :value="animal.id"
              >
              {{ animal.name }} ({{ animal.type }})
            </label>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label>Выберите услуги</label>
        <div class="services-list">
          <div v-if="availableServices.length === 0" class="no-services">
            Нет доступных услуг
          </div>
          <div v-else v-for="service in availableServices" :key="service.id" class="service-item">
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
        <button type="submit" class="btn-primary" :disabled="loading || !isValid">
          {{ loading ? 'Создание...' : 'Создать бронирование' }}
        </button>
        <button type="button" class="btn-secondary" @click="$emit('close')">
          Отмена
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { api } from '../api/config'

export default {
  name: 'BookingCreateForm',
  props: {
    dogSitter: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'created'],
  setup(props, { emit }) {
    const loading = ref(false)
    const error = ref(null)
    const userAnimals = ref([])
    const availableServices = ref([])

    const formData = ref({
      start_date: '',
      end_date: '',
      animals: [],
      services: [],
      dog_sitter: props.dogSitter.id
    })

    const minDate = computed(() => {
      const today = new Date()
      return today.toISOString().split('T')[0]
    })

    const isValid = computed(() => {
      return formData.value.start_date &&
             formData.value.end_date &&
             formData.value.animals.length > 0
    })

    const getDogSitterName = () => {
      return `${props.dogSitter.first_name} ${props.dogSitter.last_name}`.trim()
    }

    const calculateTotalPrice = () => {
      if (!formData.value.start_date || !formData.value.end_date) return 0

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

      const selectedAnimals = userAnimals.value.filter(
        animal => formData.value.animals.includes(animal.id)
      )

      const animalsPrice = selectedAnimals.reduce((sum, animal) => {
        const sizePrices = {
          'Маленький': 500,
          'Средний': 700,
          'Крупный': 1000
        }
        return sum + (sizePrices[animal?.size] || 500)
      }, 0)

      return (servicesPrice + animalsPrice) * days
    }

    const fetchInitialData = async () => {
      try {
        loading.value = true
        error.value = null
        
        const [animalsResponse, servicesResponse] = await Promise.all([
          api.get('/animals/'),
          api.get('/services/')
        ])

        userAnimals.value = animalsResponse.data
        availableServices.value = servicesResponse.data
      } catch (err) {
        console.error('Ошибка при загрузке данных:', err)
        error.value = 'Не удалось загрузить необходимые данные'
      } finally {
        loading.value = false
      }
    }

    const handleSubmit = async () => {
      try {
        loading.value = true
        error.value = null

        const response = await api.post('/bookings/', formData.value)
        emit('created', response.data)
        emit('close')
      } catch (err) {
        console.error('Ошибка при создании бронирования:', err)
        error.value = err.response?.data?.error || 'Не удалось создать бронирование'
        loading.value = false
      }
    }

    // Загружаем данные при создании компонента
    fetchInitialData()

    return {
      loading,
      error,
      formData,
      userAnimals,
      availableServices,
      minDate,
      isValid,
      getDogSitterName,
      calculateTotalPrice,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.booking-create-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.form-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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

.no-animals,
.no-services {
  color: #6c757d;
  text-align: center;
  padding: 12px;
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