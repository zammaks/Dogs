<template>
  <div class="dogsitter-list">
    <h2>Список догситтеров</h2>
    <div v-if="loading">Загрузка...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else class="dogsitters-grid">
      <div v-for="sitter in dogsitters" :key="sitter.id" class="dogsitter-card">
        <h3>{{ sitter.first_name }} {{ sitter.last_name }}</h3>
        <p>{{ sitter.description }}</p>
        <p class="price">{{ sitter.price_per_day }}₽ в день</p>
        <button @click="bookSitter(sitter.id)" class="book-button">
          Забронировать
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import { endpoints } from '../api/config'

export default {
  name: 'DogSitterList',
  setup() {
    const store = useStore()
    const dogsitters = ref([])
    const loading = ref(true)
    const error = ref(null)

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

    const bookSitter = async (sitterId) => {
      // Здесь будет логика бронирования
      console.log('Бронирование догситтера:', sitterId)
    }

    onMounted(() => {
      fetchDogSitters()
    })

    return {
      dogsitters,
      loading,
      error,
      bookSitter
    }
  }
}
</script>

<style scoped>
.dogsitter-list {
  padding: 20px;
}

.dogsitters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.dogsitter-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background: white;
}

.price {
  font-weight: bold;
  color: #2c3e50;
}

.book-button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.book-button:hover {
  background-color: #3aa876;
}
</style> 