<template>
  <div class="app">
    <div class="header">
      <h1>🎨 Pixel Battle</h1>
      <div class="user-info">
        <span v-if="user">{{ user.first_name || 'Пользователь' }}</span>
        <span class="pixels-count">Ваших пикселей: {{ user?.pixels_placed || 0 }}</span>
        <span class="canvas-pixels-count" v-if="canvasStats">
          Всего на холсте: {{ canvasStats.total_pixels }} 
          ({{ canvasStats.coverage_percent }}% заполнено)
        </span>
      </div>
    </div>
    
    <div class="canvas-container" style="overflow: hidden; position: relative;">
      <canvas
        ref="canvasRef"
        @click="handleCanvasClick"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseLeave"
        @wheel.prevent="handleWheel"
        @touchstart="(e) => handleTouchStart(e, isPanMode)"
        @touchmove="(e) => handleTouchMove(e, isPanMode)"
        @touchend="handleTouchEnd"
        :style="{ cursor: isPanMode ? 'grab' : 'crosshair', touchAction: 'none' }"
      ></canvas>
      
      <div v-if="selectedColor" class="color-picker">
        <input
          type="color"
          v-model="selectedColor"
          @change="updateColor"
        />
        <span class="color-hex">{{ selectedColor }}</span>
      </div>
      
    </div>
    
    <div class="controls">
      <button 
        @click="togglePanMode" 
        class="pan-btn" 
        :class="{ active: isPanMode }"
        :title="isPanMode ? 'Режим перемещения (нажмите для рисования)' : 'Режим рисования (нажмите для перемещения)'"
      >
        {{ isPanMode ? '✋' : '✏️' }}
      </button>
      <button @click="openColorPicker" class="color-btn">
        Выбрать цвет
      </button>
      <button @click="zoomIn" class="zoom-btn">+</button>
      <button @click="zoomOut" class="zoom-btn">-</button>
      <button @click="resetView" class="reset-btn">Сброс</button>
      <button @click="toggleMusic" class="music-btn" :class="{ active: isMusicEnabled }">
        {{ isMusicEnabled ? '🔊' : '🔇' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { usePixelBattle } from './composables/usePixelBattle'
import { useWebSocket } from './composables/useWebSocket'
import { useAudio } from './composables/useAudio'

const canvasRef = ref(null)
const selectedColor = ref('#FF0000')
const user = ref(null)
const canvasStats = ref(null)
const isPanMode = ref(false) // Режим перемещения

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

const { 
  initCanvas, 
  drawPixel, 
  loadCanvas, 
  handleClick,
  zoom,
  panX,
  panY,
  resetZoom,
  zoomIn: zoomInCanvas,
  zoomOut: zoomOutCanvas,
  resetPan,
  handleWheel,
  handleTouchStart,
  handleTouchMove,
  handleTouchEnd,
  pixels: canvasPixels,
  showGrid,
  updateCanvasTransform
} = usePixelBattle(canvasRef)

// Функция для перезагрузки холста
const reloadCanvas = () => loadCanvas(API_URL)

const { connect, disconnect, onPixelUpdate } = useWebSocket(WS_URL)

const {
  isMusicEnabled,
  isSoundEnabled,
  initAudio,
  toggleMusic,
  playPixelPlaceSound,
  playErrorSound,
  cleanup: cleanupAudio
} = useAudio()

onMounted(async () => {
  // Инициализация Telegram Web App
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.ready()
    window.Telegram.WebApp.expand()
  }
  
  // Инициализация canvas
  await initCanvas()
  await loadCanvas(API_URL)
  
  // Устанавливаем начальный курсор
  if (canvasRef.value) {
    canvasRef.value.style.cursor = isPanMode.value ? 'grab' : 'crosshair'
  }
  
  // Подключение WebSocket
  connect()
  onPixelUpdate((data) => {
    drawPixel(data.x, data.y, data.color)
  })
  
  // Загрузка информации о пользователе
  await loadUserInfo()
  
  // Загрузка статистики холста
  await loadCanvasStats()
  
  // Инициализация аудио
  initAudio()
  
  // Обработчик для завершения перетаскивания при отпускании мыши вне canvas
  window.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
  disconnect()
  cleanupAudio()
  window.removeEventListener('mouseup', handleMouseUp)
})

async function loadUserInfo() {
  try {
    const initData = window.Telegram?.WebApp?.initData || ''
    const headers = {}
    if (initData) {
      headers['X-Telegram-Init-Data'] = initData
    }
    
    const response = await fetch(`${API_URL}/api/users/me`, {
      headers
    })
    if (response.ok) {
      user.value = await response.json()
    } else if (response.status === 401 && !initData) {
      // В режиме разработки без Telegram SDK создаем тестового пользователя
      console.log('Режим разработки: используется тестовый пользователь')
      user.value = {
        id: 1,
        first_name: 'Test',
        username: 'test_user',
        pixels_placed: 0
      }
    }
  } catch (error) {
    console.error('Ошибка загрузки пользователя:', error)
    // В режиме разработки создаем тестового пользователя
    if (!window.Telegram?.WebApp) {
      user.value = {
        id: 1,
        first_name: 'Test',
        username: 'test_user',
        pixels_placed: 0
      }
    }
  }
}

async function loadCanvasStats() {
  try {
    const response = await fetch(`${API_URL}/api/canvas/stats`)
    if (response.ok) {
      canvasStats.value = await response.json()
      console.log('Статистика холста:', canvasStats.value)
    }
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
  }
}

function togglePanMode() {
  isPanMode.value = !isPanMode.value
  if (canvasRef.value) {
    canvasRef.value.style.cursor = isPanMode.value ? 'grab' : 'crosshair'
  }
}

async function handleCanvasClick(event) {
  // В режиме перемещения не ставим пиксели
  if (isPanMode.value) {
    return
  }
  
  // Игнорируем клик, если это было перетаскивание
  if (isDragging) {
    return
  }
  
  const canvas = canvasRef.value
  if (!canvas) return
  
  // CSS transform: translate(panX, panY) scale(zoom) с transform-origin: top left
  // getBoundingClientRect() возвращает координаты с учетом transform
  
  const rect = canvas.getBoundingClientRect()
  
  // Координаты клика в viewport
  const viewportX = event.clientX
  const viewportY = event.clientY
  
  // Координаты относительно левого верхнего угла canvas в viewport
  // rect.left и rect.top уже включают transform (panX, panY)
  const screenX = viewportX - rect.left
  const screenY = viewportY - rect.top
  
  // Преобразуем из экранных координат (с учетом zoom) в мировые координаты (исходный canvas)
  // screenX = worldX * zoom, поэтому worldX = screenX / zoom
  const x = Math.floor(screenX / zoom.value)
  const y = Math.floor(screenY / zoom.value)
  
  // Проверка границ
  if (x < 0 || x >= 1000 || y < 0 || y >= 1000) {
    console.warn(`Клик вне границ холста: x=${x}, y=${y}, zoom=${zoom.value}, screenX=${screenX}, screenY=${screenY}`)
    return
  }
  
  console.log(`Попытка разместить пиксель: x=${x}, y=${y}, color=${selectedColor.value}, zoom=${zoom.value}, pan=(${panX.value}, ${panY.value})`)
  
  try {
    await handleClick(x, y, selectedColor.value, API_URL)
    playPixelPlaceSound() // Звук успешного размещения
    
    // Обновляем статистику после размещения
    await loadCanvasStats()
    
    // Перезагружаем холст через небольшую задержку, чтобы убедиться, что пиксель сохранен
    setTimeout(async () => {
      console.log('Перезагрузка холста после размещения пикселя...')
      await loadCanvas(API_URL)
      await loadCanvasStats()
    }, 500)
  } catch (error) {
    console.error('Ошибка размещения пикселя:', error)
    playErrorSound() // Звук ошибки
    
    // Показываем более детальное сообщение об ошибке
    const errorMessage = error.message || 'Не удалось разместить пиксель. Попробуйте позже.'
    alert(errorMessage)
  }
}

let isDragging = false
let dragStart = { x: 0, y: 0 }

function handleMouseDown(event) {
  if (event.button === 0) { // Левая кнопка мыши
    // В режиме перемещения всегда перетаскиваем
    // В режиме рисования перетаскиваем только если зажата клавиша (например, Space или специальная кнопка)
    if (isPanMode.value) {
      isDragging = true
      dragStart = { x: event.clientX, y: event.clientY }
      if (canvasRef.value) {
        canvasRef.value.style.cursor = 'grabbing'
      }
    }
    // В режиме рисования не перетаскиваем - сразу ставим пиксель
  }
}

function handleMouseMove(event) {
  if (isDragging) {
    const deltaX = event.clientX - dragStart.x
    const deltaY = event.clientY - dragStart.y
    panX.value += deltaX
    panY.value += deltaY
    dragStart = { x: event.clientX, y: event.clientY }
    updateCanvasTransform()
  }
}

function handleMouseUp(event) {
  if (isDragging) {
    isDragging = false
    if (canvasRef.value) {
      canvasRef.value.style.cursor = isPanMode.value ? 'grab' : 'crosshair'
    }
    // Не обрабатываем клик, если было перетаскивание
    event.preventDefault()
    event.stopPropagation()
  }
}

function handleMouseLeave() {
  isDragging = false
  if (canvasRef.value) {
    canvasRef.value.style.cursor = isPanMode.value ? 'grab' : 'crosshair'
  }
}

function openColorPicker() {
  // Цвет уже выбран через input type="color"
}

function updateColor() {
  // Цвет обновлен
}

function zoomIn() {
  zoomInCanvas()
}

function zoomOut() {
  zoomOutCanvas()
}

function resetView() {
  resetZoom()
  resetPan()
}
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}

.header {
  padding: 10px;
  background: var(--tg-theme-header-bg-color, #ffffff);
  border-bottom: 1px solid var(--tg-theme-hint-color, #e0e0e0);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  font-size: 20px;
  font-weight: bold;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 12px;
}

.pixels-count {
  color: var(--tg-theme-hint-color, #999999);
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #f0f0f0;
}

canvas {
  display: block;
  cursor: crosshair;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}

.color-picker {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-picker input[type="color"] {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.color-hex {
  font-family: monospace;
  font-size: 14px;
}


.controls {
  padding: 10px;
  background: var(--tg-theme-bg-color, #ffffff);
  border-top: 1px solid var(--tg-theme-hint-color, #e0e0e0);
  display: flex;
  gap: 10px;
  justify-content: center;
}

button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  background: var(--tg-theme-button-color, #3390ec);
  color: var(--tg-theme-button-text-color, #ffffff);
}

button:active {
  opacity: 0.8;
}

.zoom-btn {
  width: 40px;
  height: 40px;
  font-size: 20px;
  font-weight: bold;
}

.reset-btn {
  background: var(--tg-theme-destructive-text-color, #ff3b30);
}

.pan-btn {
  width: 40px;
  height: 40px;
  font-size: 20px;
  background: var(--tg-theme-button-color, #3390ec);
  opacity: 0.7;
}

.pan-btn.active {
  opacity: 1;
  background: var(--tg-theme-button-color, #3390ec);
  border: 2px solid var(--tg-theme-text-color, #000000);
}

.music-btn {
  width: 40px;
  height: 40px;
  font-size: 20px;
  background: var(--tg-theme-button-color, #3390ec);
  opacity: 0.7;
}

.music-btn.active {
  opacity: 1;
}
</style>
