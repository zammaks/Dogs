<template>
  <div class="my-animals">
    <div class="header">
      <h1>Мои животные</h1>
      <button class="btn btn-primary" @click="showModal = true">
        Добавить животное
      </button>
    </div>

    <!-- Индикатор загрузки -->
    <div v-if="loading" class="loading">
      Загрузка...
    </div>

    <!-- Сообщение об ошибке -->
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- Для администратора -->
    <div v-else-if="isAdmin" class="admin-animals">
      <div v-for="user in userAnimals" :key="user.id" class="user-animals-section">
        <h3 class="user-header">{{ user.first_name }} {{ user.last_name }} ({{ user.email }})</h3>
        <div v-if="user.animals.length === 0" class="no-animals">
          У пользователя нет животных
        </div>
        <div v-else class="animals-list">
          <div v-for="animal in user.animals" :key="animal.id" class="animal-card" @click="viewAnimalDetails(animal.id)">
            <div class="animal-photo">
              <img v-if="animal.photo" :src="getPhotoUrl(animal.photo)" :alt="animal.name">
              <img v-else :src="getDefaultAnimalPhoto(animal.type)" :alt="animal.name">
            </div>
            <h3>{{ animal.name }}</h3>
            <div class="animal-info">
              <p><strong>Тип:</strong> {{ getAnimalType(animal.type) }}</p>
              <p><strong>Порода:</strong> {{ animal.breed }}</p>
              <p><strong>Возраст:</strong> {{ getAgeString(animal.age) }}</p>
              <p><strong>Бронирований:</strong> {{ animal.bookings_count }}</p>
            </div>
            <div class="button-group">
              <button class="btn btn-primary" @click.stop="editAnimal(animal)">
                Редактировать
              </button>
              <button class="btn btn-danger" @click.stop="openDeleteModal(animal)">
                Удалить
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Для обычного пользователя -->
    <div v-else>
      <div v-if="animals.length === 0" class="no-animals">
        <p>У вас пока нет добавленных животных</p>
      </div>
      <div v-else class="animals-list">
        <div v-for="animal in animals" :key="animal.id" class="animal-card" @click="viewAnimalDetails(animal.id)">
          <div class="animal-photo">
            <img v-if="animal.photo" :src="getPhotoUrl(animal.photo)" :alt="animal.name">
            <img v-else :src="getDefaultAnimalPhoto(animal.type)" :alt="animal.name">
          </div>
          <h3>{{ animal.name }}</h3>
          <div class="animal-info">
            <p><strong>Тип:</strong> {{ getAnimalType(animal.type) }}</p>
            <p><strong>Порода:</strong> {{ animal.breed }}</p>
            <p><strong>Возраст:</strong> {{ getAgeString(animal.age) }}</p>
          </div>
          <div class="button-group">
            <button class="btn btn-primary" @click.stop="editAnimal(animal)">
              Редактировать
            </button>
            <button class="btn btn-danger" @click.stop="openDeleteModal(animal)">
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно добавления/редактирования животного -->
    <div v-if="showModal" class="modal" @click.self="closeModal" @keydown.esc="closeModal" tabindex="0">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ isEditing ? 'Редактировать животное' : 'Добавить животное' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="submitAnimalForm" class="animal-form">
          <div class="form-fields">
            <div class="form-group">
              <label>Кличка:</label>
              <input v-model="animalForm.name" type="text" required>
            </div>
            <div class="form-group">
              <label>Тип:</label>
              <select v-model="animalForm.type" required>
                <option value="dog">Собака</option>
                <option value="cat">Кошка</option>
                <option value="other">Другое</option>
              </select>
            </div>
            <div class="form-group">
              <label>Порода:</label>
              <input v-model="animalForm.breed" type="text" required>
            </div>
            <div class="form-group">
              <label>Размер:</label>
              <select v-model="animalForm.size" required>
                <option value="small">Маленький</option>
                <option value="medium">Средний</option>
                <option value="large">Большой</option>
              </select>
            </div>
            <div class="form-group">
              <label>Возраст:</label>
              <input v-model.number="animalForm.age" type="number" min="0" required>
            </div>
            <div class="form-group">
              <label>Особенности:</label>
              <textarea 
                v-model="animalForm.special_needs" 
                required 
                rows="3" 
                placeholder="Опишите особенности вашего питомца"
              ></textarea>
            </div>
            <div class="form-group">
              <label>Фотография:</label>
              <div class="photo-preview-container">
                <div class="photo-preview" v-if="photoPreview || (isEditing && !animalForm.photo)">
                  <img :src="photoPreview || (isEditing ? getPhotoUrl(animals.find(a => a.id === editingAnimalId)?.photo) : null) || getDefaultAnimalPhoto(animalForm.type)" alt="Предпросмотр">
                </div>
                <div class="photo-upload">
                  <input type="file" @change="handleFileUpload" accept="image/*" ref="fileInput">
                  <button type="button" class="btn btn-secondary" @click="clearPhoto" v-if="animalForm.photo || photoPreview">
                    Очистить фото
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">
              Отмена
            </button>
            <button type="submit" class="btn btn-primary">
              {{ isEditing ? 'Сохранить' : 'Добавить' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Модальное окно подтверждения удаления -->
    <div v-if="showDeleteModal" class="modal" @click.self="closeDeleteModal" @keydown.esc="closeDeleteModal" tabindex="0">
      <div class="modal-content delete-modal">
        <div class="modal-header">
          <h2>Подтверждение удаления</h2>
          <button class="close-btn" @click="closeDeleteModal">&times;</button>
        </div>
        <div class="modal-body">
          <p>Вы действительно хотите удалить животное:</p>
          <p class="animal-delete-info">
            <strong>{{ animalToDelete?.name }}</strong>
            <span>({{ getAgeString(animalToDelete?.age) }})</span>
          </p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="closeDeleteModal">
            Отмена
          </button>
          <button type="button" class="btn btn-danger" @click="confirmDelete">
            Удалить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'

export default {
  name: 'MyAnimals',
  setup() {
    const store = useStore()
    const router = useRouter()
    const animals = ref([])
    const userAnimals = ref([]) // Для администратора
    const showModal = ref(false)
    const loading = ref(false)
    const error = ref(null)
    const isEditing = ref(false)
    const editingAnimalId = ref(null)
    const photoPreview = ref(null)
    const showDeleteModal = ref(false)
    const animalToDelete = ref(null)
    
    const animalForm = ref({
      name: '',
      type: 'dog',
      breed: '',
      size: 'medium',
      age: 0,
      special_needs: '',
      photo: null
    })

    const isAdmin = computed(() => store.state.auth.user?.is_superuser)

    // Настройка axios
    const token = localStorage.getItem('token')
    const api = axios.create({
      baseURL: 'http://localhost:8000',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json'
      }
    })

    const getPhotoUrl = (photoPath) => {
      if (!photoPath) return null
      // Если путь уже начинается с http или https, возвращаем как есть
      if (photoPath.startsWith('http')) {
        return photoPath
      }
      // Если путь начинается с /media/, убираем /media/
      const path = photoPath.startsWith('/media/') ? photoPath.substring(7) : photoPath
      return `http://localhost:8000/media/${path}`
    }

    const handleFileUpload = (event) => {
      const file = event.target.files[0]
      if (file) {
        animalForm.value.photo = file
        const reader = new FileReader()
        reader.onload = (e) => {
          photoPreview.value = e.target.result
        }
        reader.readAsDataURL(file)
      }
    }

    const clearPhoto = () => {
      animalForm.value.photo = null
      photoPreview.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const fetchAnimals = async () => {
      loading.value = true
      error.value = null
      try {
        if (isAdmin.value) {
          // Для администратора получаем животных по пользователям
          const response = await api.get('/api/animals-by-user/')
          userAnimals.value = response.data
        } else {
          // Для обычного пользователя получаем только его животных
          const response = await api.get('/api/animals/')
          animals.value = response.data
        }
      } catch (err) {
        console.error('Ошибка при получении списка животных:', err)
        if (err.response?.status === 403) {
          error.value = 'У вас нет прав для просмотра этой информации'
        } else {
          error.value = 'Не удалось загрузить список животных. Пожалуйста, попробуйте позже.'
        }
      } finally {
        loading.value = false
      }
    }

    const editAnimal = (animal) => {
      isEditing.value = true
      editingAnimalId.value = animal.id
      animalForm.value = {
        name: animal.name,
        type: animal.type,
        breed: animal.breed,
        size: animal.size,
        age: animal.age,
        special_needs: animal.special_needs || '',
        photo: null
      }
      if (animal.photo) {
        photoPreview.value = getPhotoUrl(animal.photo)
      }
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      isEditing.value = false
      editingAnimalId.value = null
      photoPreview.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      animalForm.value = {
        name: '',
        type: 'dog',
        breed: '',
        size: 'medium',
        age: 0,
        special_needs: '',
        photo: null
      }
    }

    const submitAnimalForm = async () => {
      try {
        const formData = new FormData()
        formData.append('name', animalForm.value.name)
        formData.append('type', animalForm.value.type)
        formData.append('breed', animalForm.value.breed)
        formData.append('size', animalForm.value.size)
        formData.append('age', animalForm.value.age)
        formData.append('special_needs', animalForm.value.special_needs)
        
        if (animalForm.value.photo) {
          formData.append('photo', animalForm.value.photo)
        }

        const headers = {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }

        if (isEditing.value) {
          await api.put(`/api/animals/${editingAnimalId.value}/`, formData, { headers })
        } else {
          await api.post('/api/animals/', formData, { headers })
        }

        await fetchAnimals()
        closeModal()
      } catch (error) {
        console.error('Ошибка при сохранении животного:', error)
      }
    }

    const openDeleteModal = (animal) => {
      animalToDelete.value = animal
      showDeleteModal.value = true
    }

    const closeDeleteModal = () => {
      showDeleteModal.value = false
      animalToDelete.value = null
    }

    const confirmDelete = async () => {
      try {
        await api.delete(`/api/animals/${animalToDelete.value.id}/`)
        await fetchAnimals()
        closeDeleteModal()
      } catch (error) {
        console.error('Ошибка при удалении животного:', error)
      }
    }

    const getAnimalType = (type) => {
      const types = {
        dog: 'Собака',
        cat: 'Кошка',
        other: 'Другое'
      }
      return types[type] || type
    }

    const getAgeString = (age) => {
      if (age === 0) return 'Менее года'
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

    const getDefaultAnimalPhoto = (type) => {
      switch (type) {
        case 'dog':
          return '/images/default-dog.jpg'
        case 'cat':
          return '/images/default-cat.jpg'
        default:
          return '/images/default-pet.jpg'
      }
    }

    const fileInput = ref(null)

    const viewAnimalDetails = (animalId) => {
      router.push(`/my-animals/${animalId}`)
    }

    onMounted(() => {
      fetchAnimals()
      // Добавляем обработчик Esc при монтировании
      document.addEventListener('keydown', handleEscKey)
    })

    onUnmounted(() => {
      // Удаляем обработчик при размонтировании
      document.removeEventListener('keydown', handleEscKey)
    })

    const handleEscKey = (event) => {
      if (event.key === 'Escape' && showModal.value) {
        closeModal()
      }
    }

    return {
      animals,
      userAnimals,
      showModal,
      loading,
      error,
      animalForm,
      isEditing,
      editAnimal,
      closeModal,
      submitAnimalForm,
      openDeleteModal,
      getAnimalType,
      getAgeString,
      handleFileUpload,
      getPhotoUrl,
      getDefaultAnimalPhoto,
      photoPreview,
      clearPhoto,
      fileInput,
      handleEscKey,
      showDeleteModal,
      closeDeleteModal,
      confirmDelete,
      animalToDelete,
      viewAnimalDetails,
      isAdmin
    }
  }
}
</script>

<style scoped>
.my-animals {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 20px;
}

.header .btn-primary {
  padding: 15px 30px;
  font-size: 18px;
  min-width: 250px;
  height: 55px;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .header h1 {
    margin: 0;
    font-size: 24px;
  }

  .header .btn-primary {
    padding: 12px 20px;
    font-size: 16px;
    min-width: 200px;
    height: 45px;
  }
}

.animals-list {
  display: flex;
  flex-wrap: wrap;
  gap: 100px;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  justify-content: center;
}

.animal-card {
  flex: 0 0 auto;
  width: 300px;
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 15px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.animal-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.animal-photo {
  width: 100%;
  height: 300px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
}

.animal-photo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.animal-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-grow: 1;
}

.animal-info p {
  margin: 0;
  line-height: 1.4;
}

.animal-card h3 {
  margin: 0;
  font-size: 1.3em;
  color: #2c3e50;
}

.no-animals {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  outline: none;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 95%;
  max-width: 600px;
  min-width: 320px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  display: flex;
  flex-direction: column;
}

.modal-header {
  position: relative;
  padding-bottom: 15px;
  margin-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.close-btn {
  position: absolute;
  top: 0;
  right: 0;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: 0 5px;
  line-height: 1;
}

.close-btn:hover {
  color: #dc3545;
}

.animal-form {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.form-fields {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 5px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 0;
  width: 100%;
}

.form-group label {
  font-weight: 500;
  color: #2c3e50;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background-color: #fff;
  box-sizing: border-box;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.1);
}

.modal-footer {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: center;
  gap: 15px;
  position: static;
  background: none;
}

.modal-footer .btn {
  min-width: 140px;
  padding: 12px 24px;
  font-size: 16px;
}

.btn-primary {
  background: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

.btn-secondary {
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-danger {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: #3aa876;
  transform: translateY(-1px);
}

.btn-secondary:hover,
.btn-danger:hover {
  background: #c82333;
  transform: translateY(-1px);
}

.btn-primary:active,
.btn-secondary:active,
.btn-danger:active {
  transform: translateY(0);
}

.loading {
  text-align: center;
  padding: 20px;
  font-size: 18px;
  color: #666;
}

.error-message {
  text-align: center;
  padding: 20px;
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  margin: 20px 0;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: auto;
  padding-top: 15px;
}

.button-group .btn {
  flex: 1;
  padding: 12px 20px;
  font-size: 15px;
  height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo-preview-container {
  margin-top: 5px;
  width: 100%;
  box-sizing: border-box;
}

.photo-preview {
  width: 100%;
  height: 150px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
}

.photo-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.photo-upload {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.photo-upload input[type="file"] {
  flex: 1;
}

/* Стилизация скроллбара */
.modal-content::-webkit-scrollbar {
  width: 8px;
}

.modal-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.modal-content::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.modal-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.modal-body {
  padding: 20px 0;
  text-align: center;
  font-size: 16px;
}

@media (max-width: 1200px) {
  .animals-list {
    max-width: 950px;
  }
}

@media (max-width: 999px) {
  .animals-list {
    max-width: 625px;
  }
}

@media (max-width: 680px) {
  .animals-list {
    max-width: 300px;
  }
  
  .animal-card {
    width: 100%;
  }
}

.animal-delete-info {
  margin-top: 10px;
  font-size: 18px;
}

.animal-delete-info strong {
  color: #dc3545;
}

.animal-delete-info span {
  color: #6c757d;
  margin-left: 5px;
}

.delete-modal {
  max-width: 400px;
}

.user-animals-section {
  margin-bottom: 2rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.user-header {
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e9ecef;
  color: #343a40;
  font-size: 1.25rem;
}

.admin-animals {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.admin-animals .animals-list {
  padding: 1rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
</style> 