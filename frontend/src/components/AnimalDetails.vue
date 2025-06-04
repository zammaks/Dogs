<template>
  <div class="animal-details" v-if="animal">
    <div class="container">
      <div class="back-button">
        <button class="btn btn-secondary" @click="goBack">
          &larr; Вернуться к списку животных
        </button>
      </div>

      <div class="animal-header">
        <h1>{{ animal.name }}</h1>
        <div class="animal-photo">
          <img v-if="animal.photo" :src="getPhotoUrl(animal.photo)" :alt="animal.name">
          <img v-else :src="getDefaultAnimalPhoto(animal.type)" :alt="animal.name">
        </div>
      </div>

      <div class="animal-info">
        <div class="info-item">
          <h3>Тип животного:</h3>
          <p>{{ getAnimalType(animal.type) }}</p>
        </div>
        <div class="info-item">
          <h3>Порода:</h3>
          <p>{{ animal.breed }}</p>
        </div>
        <div class="info-item">
          <h3>Возраст:</h3>
          <p>{{ getAgeString(animal.age) }}</p>
        </div>
        <div class="info-item">
          <h3>Размер:</h3>
          <p>{{ getSizeString(animal.size) }}</p>
        </div>
        <div class="info-item">
          <h3>Особенности:</h3>
          <p>{{ animal.special_needs }}</p>
        </div>
      </div>

      <div class="action-buttons">
        <button class="btn btn-primary" @click="editAnimal">
          Редактировать
        </button>
        <button class="btn btn-danger" @click="openDeleteModal">
          Удалить
        </button>
      </div>
    </div>

    <!-- Модальное окно редактирования животного -->
    <div v-if="showEditModal" class="modal" @click.self="closeEditModal" @keydown.esc="closeEditModal" tabindex="0">
      <div class="modal-content edit-modal">
        <div class="modal-header">
          <h2>Редактировать животное</h2>
          <button class="close-btn" @click="closeEditModal">&times;</button>
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
                <div class="photo-preview" v-if="photoPreview || animalForm.photo">
                  <img :src="photoPreview || getPhotoUrl(animalForm.photo)" alt="Предпросмотр">
                </div>
                <div class="photo-upload">
                  <input type="file" @change="handleFileUpload" accept="image/*" ref="fileInput">
                  <button type="button" class="btn btn-secondary" @click="clearPhoto" v-if="photoPreview || animalForm.photo">
                    Очистить фото
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeEditModal">
              Отмена
            </button>
            <button type="submit" class="btn btn-primary">
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Модальное окно подтверждения удаления -->
    <div v-if="showDeleteModal" class="modal" @click.self="closeDeleteModal">
      <div class="modal-content delete-modal">
        <div class="modal-header">
          <h2>Подтверждение удаления</h2>
          <button class="close-btn" @click="closeDeleteModal">&times;</button>
        </div>
        <div class="modal-body">
          <p>Вы действительно хотите удалить животное:</p>
          <p class="animal-delete-info">
            <strong>{{ animal.name }}</strong>
            <span>({{ getAgeString(animal.age) }})</span>
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeDeleteModal">
            Отмена
          </button>
          <button class="btn btn-danger" @click="confirmDelete">
            Удалить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'AnimalDetails',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const animal = ref(null)
    const showDeleteModal = ref(false)
    const showEditModal = ref(false)
    const photoPreview = ref(null)
    const fileInput = ref(null)
    const animalForm = ref({
      name: '',
      type: 'dog',
      breed: '',
      size: 'medium',
      age: 0,
      special_needs: '',
      photo: null
    })

    const api = axios.create({
      baseURL: 'http://localhost:8000',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    })

    const fetchAnimal = async () => {
      try {
        const response = await api.get(`/api/animals/${route.params.id}/`)
        animal.value = response.data
      } catch (error) {
        console.error('Ошибка при получении данных о животном:', error)
        router.push('/my-animals')
      }
    }

    const getPhotoUrl = (photoPath) => {
      if (!photoPath) return null
      if (photoPath.startsWith('http')) {
        return photoPath
      }
      const path = photoPath.startsWith('/') ? photoPath.substring(1) : photoPath
      return `http://localhost:8000/media/${path}`
    }

    const getDefaultAnimalPhoto = (type) => {
      switch (type) {
        case 'dog':
          return '/images/собака.jpg'
        case 'cat':
          return '/images/кот.png'
        default:
          return '/images/собака.jpg'
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

    const getSizeString = (size) => {
      const sizes = {
        small: 'Маленький',
        medium: 'Средний',
        large: 'Большой'
      }
      return sizes[size] || size
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

    const editAnimal = () => {
      animalForm.value = {
        name: animal.value.name,
        type: animal.value.type,
        breed: animal.value.breed,
        size: animal.value.size,
        age: animal.value.age,
        special_needs: animal.value.special_needs,
        photo: animal.value.photo
      }
      showEditModal.value = true
    }

    const openDeleteModal = () => {
      showDeleteModal.value = true
    }

    const closeDeleteModal = () => {
      showDeleteModal.value = false
    }

    const confirmDelete = async () => {
      try {
        await api.delete(`/api/animals/${animal.value.id}/`)
        router.push('/my-animals')
      } catch (error) {
        console.error('Ошибка при удалении животного:', error)
      }
    }

    const goBack = () => {
      router.push('/my-animals')
    }

    const closeEditModal = () => {
      showEditModal.value = false
      photoPreview.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
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

    const submitAnimalForm = async () => {
      try {
        const formData = new FormData()
        formData.append('name', animalForm.value.name)
        formData.append('type', animalForm.value.type)
        formData.append('breed', animalForm.value.breed)
        formData.append('size', animalForm.value.size)
        formData.append('age', animalForm.value.age)
        formData.append('special_needs', animalForm.value.special_needs)
        
        if (animalForm.value.photo instanceof File) {
          formData.append('photo', animalForm.value.photo)
        }

        const headers = {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }

        await api.put(`/api/animals/${animal.value.id}/`, formData, { headers })
        await fetchAnimal() // Обновляем данные на странице
        closeEditModal()
      } catch (error) {
        console.error('Ошибка при сохранении животного:', error)
      }
    }

    onMounted(() => {
      fetchAnimal()
    })

    return {
      animal,
      getPhotoUrl,
      getDefaultAnimalPhoto,
      getAnimalType,
      getSizeString,
      getAgeString,
      editAnimal,
      showDeleteModal,
      openDeleteModal,
      closeDeleteModal,
      confirmDelete,
      goBack,
      showEditModal,
      closeEditModal,
      animalForm,
      handleFileUpload,
      clearPhoto,
      photoPreview,
      fileInput,
      submitAnimalForm
    }
  }
}
</script>

<style scoped>
.animal-details {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.container {
  position: relative;
  background: white;
  border-radius: 12px;
  padding: 30px;
  padding-top: 80px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.animal-header {
  text-align: center;
  margin-bottom: 30px;
}

.animal-header h1 {
  font-size: 2.5em;
  color: #2c3e50;
  margin-bottom: 20px;
}

.animal-photo {
  width: 100%;
  max-width: 500px;
  height: 400px;
  margin: 0 auto;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.animal-photo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.animal-info {
  margin: 30px 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.info-item {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.info-item h3 {
  color: #42b983;
  margin: 0 0 10px 0;
  font-size: 1.2em;
}

.info-item p {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1em;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}

.btn {
  padding: 12px 30px;
  font-size: 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 180px;
}

.btn-primary {
  background: #42b983;
  color: white;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn:hover {
  transform: translateY(-2px);
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
  align-items: flex-start;
  z-index: 1000;
  overflow-y: auto;
  padding: 20px;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 95%;
  max-width: 400px;
  margin: auto;
  position: relative;
}

.edit-modal {
  max-width: 600px;
  margin: 40px auto;
}

.modal-header {
  position: relative;
  margin-bottom: 20px;
  padding-bottom: 15px;
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
  color: #666;
}

.close-btn:hover {
  color: #dc3545;
}

.form-fields {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  padding-right: 10px;
}

.form-fields::-webkit-scrollbar {
  width: 8px;
}

.form-fields::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.form-fields::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.form-fields::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.modal-body {
  text-align: center;
  margin-bottom: 20px;
}

.modal-footer {
  display: flex;
  justify-content: center;
  gap: 15px;
}

.btn-secondary {
  background: #6c757d;
  color: white;
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

.back-button {
  position: absolute;
  top: 20px;
  left: 20px;
}

.back-button .btn {
  font-size: 16px;
  padding: 10px 20px;
  background-color: #f8f9fa;
  color: #2c3e50;
  border: 1px solid #dee2e6;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.back-button .btn:hover {
  background-color: #e9ecef;
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .back-button {
    position: static;
    margin-bottom: 20px;
    text-align: left;
  }

  .container {
    padding-top: 30px;
  }

  .animal-details {
    padding: 10px;
  }

  .container {
    padding: 15px;
  }

  .animal-header h1 {
    font-size: 2em;
  }

  .animal-photo {
    height: 300px;
  }

  .btn {
    padding: 10px 20px;
    min-width: 140px;
  }

  .back-button .btn {
    font-size: 16px;
    padding: 12px 20px;
  }

  .modal {
    padding: 10px;
  }

  .edit-modal {
    margin: 20px auto;
  }

  .form-fields {
    max-height: calc(100vh - 160px);
  }
}

.animal-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: 500;
  color: #2c3e50;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.photo-preview-container {
  margin-top: 10px;
}

.photo-preview {
  width: 100%;
  height: 200px;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.photo-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.photo-upload {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style> 