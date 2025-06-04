<template>
  <div class="accessibility">
    <button @click="togglePanel" class="accessibility-toggle" :title="'Версия для слабовидящих'">
      <svg class="accessibility-icon" viewBox="0 0 24 24" width="24" height="24">
        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" fill="currentColor"/>
      </svg>
    </button>

    <div v-if="showPanel" class="accessibility-panel">
      <div class="panel-header">
        <h3>Специальные возможности</h3>
        <button @click="togglePanel" class="close-button" title="Закрыть">×</button>
      </div>
      
      <div class="accessibility-section">
        <h4>Размер шрифта</h4>
        <div class="font-size-controls">
          <button 
            @click="setFontSize('small')" 
            :class="{ active: settings.fontSize === 'small' }"
            title="Мелкий шрифт"
            class="font-button"
          >A</button>
          <button 
            @click="setFontSize('medium')" 
            :class="{ active: settings.fontSize === 'medium' }"
            title="Средний шрифт"
            class="font-button"
          >A</button>
          <button 
            @click="setFontSize('large')" 
            :class="{ active: settings.fontSize === 'large' }"
            title="Крупный шрифт"
            class="font-button"
          >A</button>
        </div>
      </div>

      <div class="accessibility-section">
        <h4>Цветовая схема</h4>
        <div class="color-scheme-controls">
          <button 
            @click="setColorScheme('default')" 
            :class="{ active: settings.colorScheme === 'default' }"
          >
            Обычная
          </button>
          <button 
            @click="setColorScheme('high-contrast')" 
            :class="{ active: settings.colorScheme === 'high-contrast' }"
          >
            Контраст
          </button>
          <button 
            @click="setColorScheme('black-white')" 
            :class="{ active: settings.colorScheme === 'black-white' }"
          >
            Ч/Б
          </button>
          <button 
            @click="setColorScheme('dark')" 
            :class="{ active: settings.colorScheme === 'dark' }"
          >
            Тёмная
          </button>
        </div>
      </div>

      <div class="accessibility-section">
        <div class="images-control">
          <label class="switch" title="Переключить отображение изображений">
            <input 
              type="checkbox" 
              :checked="!isImagesHidden"
              @change="toggleImages"
            >
            <span class="slider"></span>
          </label>
          <span class="control-label">Изображения</span>
        </div>
      </div>

      <button @click="resetSettings" class="reset-button" title="Вернуть стандартные настройки">
        Сбросить
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'

export default {
  name: 'Accessibility',
  setup() {
    const showPanel = ref(false)
    const isImagesHidden = ref(false)
    
    const settings = reactive({
      fontSize: 'medium',
      colorScheme: 'default'
    })

    const loadSettings = () => {
      const savedSettings = localStorage.getItem('accessibilitySettings')
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings)
        settings.fontSize = parsed.fontSize
        settings.colorScheme = parsed.colorScheme
        isImagesHidden.value = parsed.isImagesHidden || false
        applySettings()
      }
    }

    const saveSettings = () => {
      localStorage.setItem('accessibilitySettings', JSON.stringify({
        ...settings,
        isImagesHidden: isImagesHidden.value
      }))
    }

    const applySettings = () => {
      document.documentElement.setAttribute('data-font-size', settings.fontSize)
      document.documentElement.setAttribute('data-color-scheme', settings.colorScheme)
      
      if (isImagesHidden.value) {
        document.documentElement.classList.add('hide-images')
      } else {
        document.documentElement.classList.remove('hide-images')
      }
    }

    const togglePanel = () => {
      showPanel.value = !showPanel.value
    }

    const setFontSize = (size) => {
      settings.fontSize = size
      saveSettings()
      applySettings()
    }

    const setColorScheme = (scheme) => {
      settings.colorScheme = scheme
      saveSettings()
      applySettings()
    }

    const toggleImages = () => {
      isImagesHidden.value = !isImagesHidden.value
      saveSettings()
      applySettings()
    }

    const resetSettings = () => {
      settings.fontSize = 'medium'
      settings.colorScheme = 'default'
      isImagesHidden.value = false
      showPanel.value = false
      saveSettings()
      applySettings()
    }

    onMounted(() => {
      loadSettings()
    })

    return {
      showPanel,
      settings,
      isImagesHidden,
      togglePanel,
      setFontSize,
      setColorScheme,
      toggleImages,
      resetSettings
    }
  }
}
</script>

<style>
/* Глобальные стили для настроек доступности */
:root[data-font-size="small"] {
  --base-font-size: 14px;
}

:root[data-font-size="medium"] {
  --base-font-size: 16px;
}

:root[data-font-size="large"] {
  --base-font-size: 20px;
}

:root[data-color-scheme="default"] {
  --background-color: #ffffff;
  --text-color: #2c3e50;
  --primary-color: #42b983;
}

:root[data-color-scheme="high-contrast"] {
  --background-color: #000000;
  --text-color: #ffffff;
  --primary-color: #ffff00;
}

:root[data-color-scheme="black-white"] {
  --background-color: #ffffff;
  --text-color: #000000;
  --primary-color: #2c3e50;
}

:root[data-color-scheme="dark"] {
  --background-color: #1a1a1a;
  --text-color: #ffffff;
  --primary-color: #42b983;
}

:root[data-color-scheme="light"] {
  --background-color: #ffffff;
  --text-color: #000000;
  --primary-color: #2c3e50;
}

:root[data-show-images="false"] img {
  display: none !important;
}

/* Стили компонента */
.accessibility {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1100;
}

.accessibility-toggle {
  background: var(--primary-color);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  color: var(--button-text);
  padding: 8px;
}

.accessibility-toggle:hover {
  transform: scale(1.05);
}

.accessibility-icon {
  width: 24px;
  height: 24px;
}

.accessibility-panel {
  position: absolute;
  top: 50px;
  right: 0;
  background: var(--background-color);
  border-radius: 8px;
  padding: 12px;
  width: 280px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-color);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-color);
}

.close-button {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-color);
  cursor: pointer;
  padding: 0 4px;
}

.accessibility-section {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.accessibility-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.accessibility-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--text-color);
}

.font-size-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.font-button {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--background-color);
  color: var(--text-color);
  transition: all 0.2s ease;
  width: 32px;
  height: 32px;
  padding: 0;
}

.font-button:nth-child(1) { 
  font-size: 12px;
  width: 28px;
  height: 28px;
}

.font-button:nth-child(2) { 
  font-size: 16px;
  width: 32px;
  height: 32px;
}

.font-button:nth-child(3) { 
  font-size: 20px;
  width: 36px;
  height: 36px;
}

.font-button:hover {
  border-color: var(--primary-color);
}

.font-button.active {
  background-color: var(--primary-color);
  color: var(--button-text);
  border-color: var(--primary-color);
}

.color-scheme-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.color-scheme-controls button {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--background-color);
  color: var(--text-color);
  font-size: 14px;
  transition: all 0.2s ease;
  flex: 1;
  min-width: 80px;
  text-align: center;
}

.color-scheme-controls button:hover {
  border-color: var(--primary-color);
}

.color-scheme-controls button.active {
  background-color: var(--primary-color);
  color: var(--button-text);
  border-color: var(--primary-color);
}

.images-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 14px;
  color: var(--text-color);
}

.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: .4s;
  border-radius: 24px;
  border: 1px solid var(--border-color);
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background-color: var(--background-color);
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--primary-color);
}

input:checked + .slider:before {
  transform: translateX(16px);
}

button.active {
  background-color: var(--primary-color);
  color: var(--button-text);
}

.reset-button {
  width: 100%;
  padding: 8px;
  margin-top: 12px;
  background: var(--primary-color);
  color: var(--button-text);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.reset-button:hover {
  opacity: 0.9;
}

/* Стили для скрытия изображений */
:root.hide-images img,
:root.hide-images .avatar,
:root.hide-images .photo,
:root.hide-images .image,
:root.hide-images .picture,
:root.hide-images [role="img"],
:root.hide-images svg:not(.accessibility-icon) {
  display: none !important;
}

:root.hide-images .image-container,
:root.hide-images .avatar-container,
:root.hide-images .photo-container {
  background: var(--background-color) !important;
  border: 1px solid var(--border-color) !important;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

:root.hide-images .image-container::after,
:root.hide-images .avatar-container::after,
:root.hide-images .photo-container::after {
  content: 'Изображение скрыто';
  color: var(--text-color);
  font-size: 14px;
}
</style> 