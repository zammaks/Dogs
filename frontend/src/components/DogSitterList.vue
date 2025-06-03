<template>
  <div class="dogsitter-list">
    <h1>Список догситтеров</h1>
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка списка догситтеров...</p>
    </div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="dogsitters-grid">
      <div v-for="sitter in dogsitters" :key="sitter.id" class="dogsitter-card">
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
            <button @click="bookSitter(sitter.id)" class="book-button">
              Забронировать
            </button>
          </div>
        </div>
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
      bookSitter,
      getAgeString,
      getExperienceString,
      getPhotoUrl
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

.book-button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  transition: background-color 0.2s;
  width: 100%;
}

.book-button:hover {
  background-color: #3aa876;
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
}
</style> 