<template>
  <div class="animals-view">
    <h1>{{ isAdmin ? 'Все животные' : 'Мои животные' }}</h1>

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
              <span class="stat-value">{{ getUserAnimals(user.id).length }}</span>
              <span class="stat-label">Животных</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ getUserAnimals(user.id).filter(a => a.type === 'dog').length }}</span>
              <span class="stat-label">Собак</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ getUserAnimals(user.id).filter(a => a.type === 'cat').length }}</span>
              <span class="stat-label">Кошек</span>
            </div>
          </div>
        </div>

        <div class="animals-container">
          <div class="animals-header">
            <h3>Животные пользователя</h3>
            <button class="toggle-btn" @click="toggleUserAnimals(user.id)">
              {{ openUsers.includes(user.id) ? 'Свернуть' : 'Развернуть' }}
              <span class="dropdown-arrow" :class="{ 'open': openUsers.includes(user.id) }">▼</span>
            </button>
          </div>
          
          <div v-if="openUsers.includes(user.id)" class="animals-list">
            <div v-for="animal in getUserAnimals(user.id)" :key="animal.id" class="animal-card">
              <div class="animal-header">
                <h3>{{ animal.name }}</h3>
                <span class="animal-type">{{ getAnimalType(animal.type) }}</span>
              </div>
              <div class="animal-details">
                <div v-if="animal.photo" class="animal-photo">
                  <img :src="animal.photo" :alt="animal.name">
                </div>
                <div class="animal-info">
                  <p><strong>Порода:</strong> {{ animal.breed || 'Не указана' }}</p>
                  <p><strong>Возраст:</strong> {{ animal.age }} {{ getAgeText(animal.age) }}</p>
                  <p><strong>Размер:</strong> {{ getAnimalSize(animal.size) }}</p>
                  <p v-if="animal.special_needs"><strong>Особые потребности:</strong> {{ animal.special_needs }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="user-view">
      <div v-for="animal in animals" :key="animal.id" class="animal-card">
        <div class="animal-header">
          <h3>{{ animal.name }}</h3>
          <span class="animal-type">{{ getAnimalType(animal.type) }}</span>
        </div>
        <div class="animal-details">
          <div v-if="animal.photo" class="animal-photo">
            <img :src="animal.photo" :alt="animal.name">
          </div>
          <div class="animal-info">
            <p><strong>Порода:</strong> {{ animal.breed || 'Не указана' }}</p>
            <p><strong>Возраст:</strong> {{ animal.age }} {{ getAgeText(animal.age) }}</p>
            <p><strong>Размер:</strong> {{ getAnimalSize(animal.size) }}</p>
            <p v-if="animal.special_needs"><strong>Особые потребности:</strong> {{ animal.special_needs }}</p>
          </div>
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
  name: 'AnimalsView',
  
  setup() {
    const store = useStore()
    const animals = ref([])
    const openUsers = ref([])
    const isAdmin = computed(() => store.state.auth.user?.is_superuser)
    
    const uniqueUsers = computed(() => {
      const users = animals.value.map(animal => animal.user)
      return [...new Map(users.map(user => [user.id, user])).values()]
    })
    
    const getUserAnimals = (userId) => {
      return animals.value.filter(animal => animal.user.id === userId)
    }
    
    const toggleUserAnimals = (userId) => {
      const index = openUsers.value.indexOf(userId)
      if (index === -1) {
        openUsers.value.push(userId)
      } else {
        openUsers.value.splice(index, 1)
      }
    }
    
    const getAnimalType = (type) => {
      const typeMap = {
        'dog': 'Собака',
        'cat': 'Кошка',
        'other': 'Другое'
      }
      return typeMap[type] || type
    }
    
    const getAnimalSize = (size) => {
      const sizeMap = {
        'small': 'Маленький',
        'medium': 'Средний',
        'large': 'Большой'
      }
      return sizeMap[size] || size
    }
    
    const getAgeText = (age) => {
      const lastDigit = age % 10
      const lastTwoDigits = age % 100
      
      if (lastTwoDigits >= 11 && lastTwoDigits <= 14) {
        return 'лет'
      }
      
      switch (lastDigit) {
        case 1:
          return 'год'
        case 2:
        case 3:
        case 4:
          return 'года'
        default:
          return 'лет'
      }
    }
    
    const fetchAnimals = async () => {
      try {
        const response = await axios.get('/api/animals/')
        animals.value = response.data
      } catch (error) {
        console.error('Ошибка при загрузке животных:', error)
      }
    }
    
    onMounted(fetchAnimals)
    
    return {
      animals,
      isAdmin,
      uniqueUsers,
      openUsers,
      getUserAnimals,
      toggleUserAnimals,
      getAnimalType,
      getAnimalSize,
      getAgeText
    }
  }
}
</script>

<style scoped>
.animals-view {
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

.animals-container {
  padding: 1.5rem;
}

.animals-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.animals-header h3 {
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

.animals-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.animal-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1.25rem;
  background: white;
  transition: transform 0.2s, box-shadow 0.2s;
}

.animal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.animal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.animal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.animal-type {
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  background-color: #e3f2fd;
  color: #1976d2;
}

.animal-details {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.animal-photo {
  width: 100%;
  height: 200px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.animal-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.animal-info {
  color: #2c3e50;
}

.animal-info p {
  margin: 0.5rem 0;
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

  .animals-list {
    grid-template-columns: 1fr;
  }
}
</style> 