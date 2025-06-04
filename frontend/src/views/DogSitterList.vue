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

    <div v-if="loading" class="loading">
      Загрузка списка догситтеров...
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
    const isAuthenticated = computed(() => store.state.auth.token !== null)
    const dogsitters = ref([])
    const loading = ref(true)
    const error = ref(null)

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
        dogsitters.value = response.data
      } catch (err) {
        console.error('Ошибка при загрузке догситтеров:', err)
        error.value = 'Не удалось загрузить список догситтеров'
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchDogSitters()
    })

    return {
      dogsitters,
      loading,
      error,
      filters,
      isAuthenticated
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
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.dogsitter-card:hover {
  transform: translateY(-4px);
}

.avatar {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.info {
  padding: 20px;
}

h3 {
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
  margin-bottom: 10px;
}

.description {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.4;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  color: #dc3545;
  text-align: center;
  padding: 20px;
}
</style> 