<template>
  <div class="notifications" v-if="notifications.length">
    <div v-for="notification in notifications" 
         :key="notification.id" 
         class="notification"
         :class="{ 'fade-out': notification.fadeOut }">
      {{ notification.message }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'Notification',
  setup() {
    const store = useStore()
    const notifications = ref([])
    const socket = ref(null)
    const reconnectTimeout = ref(null)

    const addNotification = (message) => {
      console.log('Adding notification:', message)
      const id = Date.now()
      notifications.value.push({
        id,
        message,
        fadeOut: false
      })
      
      // Начинаем исчезновение через 2 секунды
      setTimeout(() => {
        const notification = notifications.value.find(n => n.id === id)
        if (notification) {
          notification.fadeOut = true
        }
      }, 2000)
      
      // Удаляем уведомление через 3 секунды
      setTimeout(() => {
        notifications.value = notifications.value.filter(n => n.id !== id)
      }, 3000)
    }

    const connectWebSocket = () => {
      if (socket.value?.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected')
        return
      }

      const token = store.state.auth.token
      if (!token) {
        console.log('No token available')
        return
      }

      try {
        // Используем secure WebSocket, если сайт на HTTPS
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
        const wsUrl = `${protocol}//${host}/ws/notifications/?token=${token}`
        
        console.log('Connecting to WebSocket:', wsUrl)
        socket.value = new WebSocket(wsUrl)
        
        socket.value.onopen = () => {
          console.log('WebSocket connected successfully')
          if (reconnectTimeout.value) {
            clearTimeout(reconnectTimeout.value)
            reconnectTimeout.value = null
          }
        }
        
        socket.value.onmessage = (event) => {
          console.log('WebSocket message received:', event.data)
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'notification' || data.message) {
              addNotification(data.message)
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }
        
        socket.value.onclose = (event) => {
          console.log('WebSocket closed:', event)
          socket.value = null
          
          // Переподключаемся через 5 секунд
          if (!reconnectTimeout.value) {
            reconnectTimeout.value = setTimeout(() => {
              console.log('Attempting to reconnect...')
              connectWebSocket()
            }, 5000)
          }
        }

        socket.value.onerror = (error) => {
          console.error('WebSocket error:', error)
        }
      } catch (error) {
        console.error('Error creating WebSocket:', error)
      }
    }

    // Следим за изменением токена
    watch(
      () => store.state.auth.token,
      (newToken) => {
        console.log('Auth token changed:', newToken ? 'Token present' : 'No token')
        if (newToken) {
          connectWebSocket()
        } else if (socket.value) {
          socket.value.close()
          socket.value = null
        }
      }
    )

    onMounted(() => {
      console.log('Notification component mounted')
      if (store.state.auth.token) {
        connectWebSocket()
      }
    })

    onBeforeUnmount(() => {
      console.log('Notification component unmounting')
      if (socket.value) {
        socket.value.close()
        socket.value = null
      }
      if (reconnectTimeout.value) {
        clearTimeout(reconnectTimeout.value)
        reconnectTimeout.value = null
      }
    })

    return {
      notifications
    }
  }
}
</script>

<style scoped>
.notifications {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification {
  background-color: #42b983;
  color: white;
  padding: 15px 25px;
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  transition: all 0.3s ease;
  opacity: 1;
  transform: translateX(0);
  min-width: 250px;
}

.notification.fade-out {
  opacity: 0;
  transform: translateX(100%);
}
</style> 