<template>
  <div class="profile-container">
    <div v-if="loading" class="loading">
      Загрузка данных...
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else class="profile-content">
      <h2>Профиль пользователя</h2>
      
      <div v-if="isEditing" class="profile-form">
        <div class="form-group">
          <label>Аватар:</label>
          <div class="avatar-upload">
            <img v-if="avatarPreview" :src="avatarPreview" alt="Предпросмотр аватара" class="avatar-preview" />
            <img v-else-if="user.avatar_url" :src="user.avatar_url" alt="Текущий аватар" class="avatar-preview" />
            <input type="file" @change="handleAvatarChange" accept="image/*" class="file-input" />
          </div>
        </div>
        <div class="form-group">
          <label>Имя:</label>
          <input v-model="editedUser.first_name" class="form-input" />
        </div>
        <div class="form-group">
          <label>Фамилия:</label>
          <input v-model="editedUser.last_name" class="form-input" />
        </div>
        <div class="form-group">
          <label>Email:</label>
          <input v-model="editedUser.email" type="email" class="form-input" disabled />
        </div>
        <div class="form-group">
          <label>Телефон:</label>
          <input v-model="editedUser.phone" class="form-input" />
        </div>
        <div class="button-group">
          <button @click="saveChanges" class="save-button" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button @click="cancelEdit" class="cancel-button">
            Отмена
          </button>
        </div>
      </div>

      <div v-else class="profile-info">
        <div class="avatar-section">
          <img v-if="user.avatar_url" :src="user.avatar_url" alt="Аватар пользователя" class="avatar" />
          <div v-else class="avatar-placeholder">Нет аватара</div>
        </div>
        <div class="info-group">
          <span class="label">Имя:</span>
          <span class="value">{{ user.first_name }}</span>
        </div>
        <div class="info-group">
          <span class="label">Фамилия:</span>
          <span class="value">{{ user.last_name }}</span>
        </div>
        <div class="info-group">
          <span class="label">Email:</span>
          <span class="value">{{ user.email }}</span>
        </div>
        <div class="info-group">
          <span class="label">Телефон:</span>
          <span class="value">{{ user.phone || 'Не указан' }}</span>
        </div>
        <div class="button-group">
          <button @click="startEdit" class="edit-button">
            Изменить данные
          </button>
          <button @click="showDeleteModal" class="delete-button">
            Удалить аккаунт
          </button>
        </div>
      </div>

      <div class="photos-section">
        <h3>Мои фотографии</h3>
        <div class="photos-grid">
          <div v-for="photo in user.photos" :key="photo.id" class="photo-item">
            <img :src="photo.photo_url" :alt="photo.description" class="photo" />
            <p class="photo-description">{{ photo.description }}</p>
            <button v-if="isEditing" @click="deletePhoto(photo.id)" class="delete-photo">Удалить</button>
          </div>
        </div>
        <div v-if="isEditing" class="photo-upload">
          <h4>Добавить новые фотографии</h4>
          <div class="upload-form">
            <input type="file" @change="handlePhotoChange" accept="image/*" multiple class="file-input" />
            <textarea v-model="newPhotoDescription" placeholder="Описание фотографии" class="photo-description-input"></textarea>
            <button @click="uploadPhoto" class="upload-button" :disabled="!selectedPhotos.length">
              Загрузить фотографии
            </button>
          </div>
        </div>
      </div>

      <!-- Модальное окно подтверждения удаления аккаунта -->
      <div v-if="showDeleteConfirmation" class="modal-overlay" @click="closeDeleteModal">
        <div class="modal-content" @click.stop>
          <h3>Подтверждение удаления аккаунта</h3>
          <div class="delete-warning">
            <p>Вы действительно хотите удалить свой аккаунт?</p>
            <p class="warning-text">Это действие необратимо. Все ваши данные, включая историю бронирований и фотографии, будут удалены.</p>
          </div>
          <div class="delete-confirmation">
            <input 
              type="text" 
              v-model="deleteConfirmationText" 
              placeholder="Введите 'УДАЛИТЬ' для подтверждения"
              class="confirmation-input"
            />
          </div>
          <div class="modal-actions">
            <button 
              @click="confirmDelete" 
              class="delete-confirm-button" 
              :disabled="deleteConfirmationText !== 'УДАЛИТЬ' || deleting"
            >
              {{ deleting ? 'Удаление...' : 'Удалить аккаунт' }}
            </button>
            <button @click="closeDeleteModal" class="cancel-button" :disabled="deleting">
              Отмена
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { api } from '../api/config'

export default {
  name: 'UserProfile',
  setup() {
    const store = useStore()
    const router = useRouter()
    const loading = ref(true)
    const error = ref(null)
    const isEditing = ref(false)
    const saving = ref(false)
    const showDeleteConfirmation = ref(false)
    const deleteConfirmationText = ref('')
    const deleting = ref(false)
    const avatarPreview = ref(null)
    const selectedPhotos = ref([])
    const newPhotoDescription = ref('')
    
    const user = ref({
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      avatar_url: null,
      photos: []
    })
    
    const editedUser = ref({})

    const handleAvatarChange = (event) => {
      const file = event.target.files[0]
      if (file) {
        // Проверяем размер файла (не более 5MB)
        if (file.size > 5 * 1024 * 1024) {
          error.value = 'Размер файла не должен превышать 5MB'
          event.target.value = ''
          return
        }
        
        // Проверяем тип файла
        if (!file.type.startsWith('image/')) {
          error.value = 'Пожалуйста, загрузите изображение'
          event.target.value = ''
          return
        }

        editedUser.value.avatar = file
        avatarPreview.value = URL.createObjectURL(file)
        error.value = null
      }
    }

    const handlePhotoChange = (event) => {
      const files = Array.from(event.target.files)
      
      // Проверяем каждый файл
      const validFiles = files.filter(file => {
        // Проверка размера
        if (file.size > 5 * 1024 * 1024) {
          error.value = `Файл ${file.name} слишком большой (максимум 5MB)`
          return false
        }
        
        // Проверка типа
        if (!file.type.startsWith('image/')) {
          error.value = `Файл ${file.name} не является изображением`
          return false
        }
        
        return true
      })

      if (validFiles.length !== files.length) {
        event.target.value = ''
        return
      }

      selectedPhotos.value = validFiles
      error.value = null
    }

    const uploadPhoto = async () => {
      if (!selectedPhotos.value.length) return

      try {
        error.value = null
        for (const photo of selectedPhotos.value) {
          const formData = new FormData()
          formData.append('photo', photo)
          formData.append('description', newPhotoDescription.value || '')
          formData.append('is_public', 'true')

          await api.post('/users/me/photos/', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
        }

        // Обновляем данные пользователя после загрузки
        await fetchUserData()
        
        // Очищаем форму
        selectedPhotos.value = []
        newPhotoDescription.value = ''
      } catch (err) {
        console.error('Error uploading photos:', err)
        error.value = err.response?.data?.message || 'Ошибка при загрузке фотографий'
      }
    }

    const deletePhoto = async (photoId) => {
      if (!confirm('Вы уверены, что хотите удалить эту фотографию?')) return

      try {
        await api.delete(`/users/me/photos/${photoId}/`)
        await fetchUserData()
      } catch (err) {
        console.error('Error deleting photo:', err)
        error.value = 'Ошибка при удалении фотографии'
      }
    }

    const fetchUserData = async () => {
      try {
        loading.value = true
        error.value = null
        const response = await api.get('/users/me/')
        user.value = response.data
      } catch (err) {
        console.error('Error fetching user data:', err)
        error.value = 'Ошибка при загрузке данных пользователя'
      } finally {
        loading.value = false
      }
    }

    const startEdit = () => {
      editedUser.value = { ...user.value }
      avatarPreview.value = null
      isEditing.value = true
    }

    const cancelEdit = () => {
      isEditing.value = false
      editedUser.value = {}
      avatarPreview.value = null
      selectedPhotos.value = []
      newPhotoDescription.value = ''
    }

    const saveChanges = async () => {
      try {
        saving.value = true
        const formData = new FormData()
        
        // Добавляем только измененные поля в formData
        if (editedUser.value.first_name) {
          formData.append('first_name', editedUser.value.first_name)
        }
        if (editedUser.value.last_name) {
          formData.append('last_name', editedUser.value.last_name)
        }
        if (editedUser.value.phone) {
          formData.append('phone', editedUser.value.phone)
        }
        if (editedUser.value.avatar instanceof File) {
          formData.append('avatar', editedUser.value.avatar)
        }

        const response = await api.patch('/users/me/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        user.value = response.data
        isEditing.value = false
        store.commit('auth/setUser', response.data)
        error.value = null
      } catch (err) {
        console.error('Error updating user data:', err)
        error.value = err.response?.data?.message || 'Ошибка при сохранении данных'
      } finally {
        saving.value = false
      }
    }

    const showDeleteModal = () => {
      showDeleteConfirmation.value = true
      deleteConfirmationText.value = ''
    }

    const closeDeleteModal = () => {
      showDeleteConfirmation.value = false
      deleteConfirmationText.value = ''
    }

    const confirmDelete = async () => {
      if (deleteConfirmationText.value !== 'УДАЛИТЬ') return

      try {
        deleting.value = true
        await api.delete('/users/me/delete/')
        
        // Выход из системы после успешного удаления
        store.dispatch('auth/logout')
        router.push('/login')
      } catch (err) {
        console.error('Error deleting account:', err)
        error.value = 'Ошибка при удалении аккаунта'
      } finally {
        deleting.value = false
        closeDeleteModal()
      }
    }

    // Загружаем данные при монтировании компонента
    fetchUserData()

    return {
      user,
      editedUser,
      loading,
      error,
      isEditing,
      saving,
      avatarPreview,
      selectedPhotos,
      newPhotoDescription,
      startEdit,
      cancelEdit,
      saveChanges,
      handleAvatarChange,
      handlePhotoChange,
      uploadPhoto,
      deletePhoto,
      showDeleteConfirmation,
      deleteConfirmationText,
      deleting,
      showDeleteModal,
      closeDeleteModal,
      confirmDelete
    }
  }
}
</script>

<style scoped>
/* Базовые стили для профиля */
.profile-container {
  padding: 20px;
  margin: 20px auto;
  max-width: 800px;
}

.profile-header,
.profile-section h2,
.profile-section h3 {
  margin-bottom: 1rem;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #dc3545;
}

.profile-content h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
  text-align: center;
}

.profile-info, .profile-form {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.info-group, .form-group {
  margin-bottom: 1.5rem;
}

.info-group {
  display: flex;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
}

.label {
  font-weight: bold;
  width: 120px;
  color: #666;
}

.value {
  flex: 1;
  color: #2c3e50;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: bold;
  color: #666;
}

.form-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-input:disabled {
  background-color: #f5f5f5;
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.edit-button, .delete-button {
  flex: 1;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.edit-button {
  background-color: #42b983;
  color: white;
}

.edit-button:hover {
  background-color: #3aa876;
}

.delete-button {
  background-color: #dc3545;
  color: white;
}

.delete-button:hover {
  background-color: #c82333;
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

.delete-warning {
  margin: 1.5rem 0;
}

.warning-text {
  color: #dc3545;
  font-weight: bold;
  margin-top: 0.5rem;
}

.delete-confirmation {
  margin: 1.5rem 0;
}

.confirmation-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.delete-confirm-button, .cancel-button {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.delete-confirm-button {
  background-color: #dc3545;
  color: white;
}

.delete-confirm-button:hover:not(:disabled) {
  background-color: #c82333;
}

.delete-confirm-button:disabled {
  background-color: #e9a8ae;
  cursor: not-allowed;
}

.cancel-button {
  background-color: #6c757d;
  color: white;
}

.cancel-button:hover:not(:disabled) {
  background-color: #5a6268;
}

.cancel-button:disabled {
  background-color: #a8a8a8;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    padding: 1.5rem;
  }
  
  .button-group {
    flex-direction: column;
  }
}

.avatar-section {
  margin-bottom: 2rem;
  text-align: center;
}

.avatar {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #42b983;
}

.avatar-placeholder {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  margin: 0 auto;
}

.avatar-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.avatar-preview {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  object-fit: cover;
}

.photos-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.photo-item {
  position: relative;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.photo {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.photo-description {
  padding: 0.5rem;
  background-color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
}

.delete-photo {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 0.8rem;
}

.photo-upload {
  margin-top: 2rem;
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 400px;
  margin: 1rem auto;
}

.photo-description-input {
  width: 100%;
  min-height: 100px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
}

.file-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
}

.upload-button {
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
}

.upload-button:disabled {
  background-color: #a8d5c2;
  cursor: not-allowed;
}

.user-info-card {
  background-color: var(--card-bg) !important;
  border: 1px solid var(--card-border) !important;
  color: var(--text-color) !important;
  padding: 2rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.profile-header,
.profile-info,
.profile-details {
  color: var(--text-color) !important;
}

.profile-section h2,
.profile-section h3,
.profile-info h1,
.profile-info h2,
.profile-details p,
.profile-details span {
  color: var(--text-color) !important;
}

:root[data-color-scheme="dark"] .profile-container,
:root[data-color-scheme="dark"] .user-info-card {
  background-color: #2c3e50 !important;
  border-color: #42b983 !important;
}

:root[data-color-scheme="dark"] .profile-header,
:root[data-color-scheme="dark"] .profile-info,
:root[data-color-scheme="dark"] .profile-details,
:root[data-color-scheme="dark"] .user-info-card * {
  color: #ffffff !important;
}

:root[data-color-scheme="high-contrast"] .profile-container,
:root[data-color-scheme="high-contrast"] .user-info-card {
  background-color: #000000 !important;
  border: 2px solid #ffffff !important;
}

:root[data-color-scheme="high-contrast"] .profile-header,
:root[data-color-scheme="high-contrast"] .profile-info,
:root[data-color-scheme="high-contrast"] .profile-details,
:root[data-color-scheme="high-contrast"] .user-info-card * {
  color: #ffffff !important;
}
</style> 