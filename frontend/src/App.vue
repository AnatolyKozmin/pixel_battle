<template>
  <div class="app">
    <div class="header">
      <button 
        @click="showGameMenu = !showGameMenu" 
        class="game-menu-btn"
        :class="{ active: currentMode === 'game' }"
      >
        🎮
      </button>
      <h1 class="gradient-text">ИТиАБД feat. ЦТ</h1>
      <div v-if="selectedColor && currentMode === 'canvas'" class="header-color-picker">
        <input
          type="color"
          v-model="selectedColor"
          @change="updateColor"
        />
      </div>
    </div>
    
    <!-- Модальное окно игры -->
    <div v-if="showGameMenu" class="game-menu-overlay" @click="showGameMenu = false">
      <div class="game-menu" @click.stop>
        <h2>🎮 Игры</h2>
        <button 
          @click="openGame('repeat')" 
          class="game-menu-item"
        >
          <span class="game-icon">🔄</span>
          <span class="game-title">Repeat Pixels</span>
          <span class="game-desc">Повтори последовательность</span>
        </button>
        <button 
          @click="openGame('pvp')" 
          class="game-menu-item"
        >
          <span class="game-icon">⚔️</span>
          <span class="game-title">PvP Battle</span>
          <span class="game-desc">Соревнуйся с оппонентом</span>
        </button>
        <button 
          @click="showGameMenu = false" 
          class="game-menu-close"
        >
          Закрыть
        </button>
      </div>
    </div>

    <!-- Холст -->
    <div v-if="currentMode === 'canvas'" class="canvas-container" ref="containerRef" style="overflow: hidden; position: relative;">
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
      
    </div>

    <!-- Игра -->
    <div v-if="currentMode === 'game'" class="game-wrapper">
      <Game :user="user" />
    </div>
    
    <!-- iOS-style Bottom Bar -->
    <div class="ios-bottom-bar">
      <div class="ios-bar-content">
        <button 
          @click="togglePanMode" 
          class="ios-btn icon-only" 
          :class="{ active: isPanMode }"
        >
          <span class="ios-icon">{{ isPanMode ? '👆' : '✏️' }}</span>
        </button>
        <button @click="zoomIn" class="ios-btn icon-only">
          <span class="ios-icon">+</span>
        </button>
        <button @click="zoomOut" class="ios-btn icon-only">
          <span class="ios-icon">−</span>
        </button>
        <button @click="toggleMusic" class="ios-btn icon-only" :class="{ active: isMusicEnabled }">
          <span class="ios-icon">{{ isMusicEnabled ? '🔊' : '🔇' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { usePixelBattle } from './composables/usePixelBattle'
import { useWebSocket } from './composables/useWebSocket'
import { useAudio } from './composables/useAudio'
import Game from './components/Game.vue'

const canvasRef = ref(null)
const containerRef = ref(null)
const selectedColor = ref('#FF0000')
const user = ref(null)
const canvasStats = ref(null)
const isPanMode = ref(false) // Режим перемещения
const currentMode = ref('canvas') // 'canvas' или 'game'
const showGameMenu = ref(false) // Показать меню игр

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002'
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8002'

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
  updateCanvasTransform,
  redrawCanvas
} = usePixelBattle(canvasRef, containerRef)

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

// Watcher для переключения режимов - перерисовываем canvas при возврате на холст
watch(currentMode, async (newMode) => {
  if (newMode === 'canvas') {
    // Ждём, пока DOM обновится
    await nextTick()
    
    // Переинициализируем canvas, если нужно
    if (canvasRef.value) {
      // Проверяем, есть ли контекст
      if (!canvasRef.value.getContext) {
        await initCanvas()
      } else {
        // Просто обновляем transform и перерисовываем
        updateCanvasTransform()
        redrawCanvas()
      }
    } else {
      // Canvas ещё не создан, инициализируем
      await initCanvas()
    }
    
    // Перезагружаем холст, чтобы получить актуальные данные
    await loadCanvas(API_URL)
    
    // Обновляем статистику
    await loadCanvasStats()
  }
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
    let errorMessage = error.message || 'Не удалось разместить пиксель. Попробуйте позже.'
    
    // Улучшенная обработка network error
    if (error.message && error.message.includes('сети')) {
      errorMessage = 'Ошибка сети. Проверьте подключение к интернету и попробуйте снова.'
    } else if (error.message && error.message.includes('timeout')) {
      errorMessage = 'Превышено время ожидания. Проверьте подключение и попробуйте снова.'
    }
    
    // Используем более дружелюбный способ показа ошибки
    if (window.Telegram?.WebApp?.showAlert) {
      window.Telegram.WebApp.showAlert(errorMessage)
    } else {
      alert(errorMessage)
    }
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

function updateColor() {
  // Цвет обновлен
}

function zoomIn() {
  zoomInCanvas()
}

function zoomOut() {
  zoomOutCanvas()
}

function openGame(gameType) {
  showGameMenu.value = false
  currentMode.value = 'game'
  // Здесь можно добавить логику для выбора типа игры, если нужно
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
  padding: 14px 10px;
  background: transparent;
  border: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  pointer-events: none; /* Позволяет кликать сквозь header */
  min-height: 60px;
}

.header > * {
  pointer-events: auto; /* Восстанавливаем кликабельность для элементов */
}

.header h1 {
  font-size: 20px;
  font-weight: bold;
  flex: 1;
  text-align: center;
  margin: 0;
  padding: 0;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
}

.gradient-text {
  background: linear-gradient(90deg, #000000 0%, #FF6B35 50%, #000000 100%);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 8s ease-in-out infinite;
  font-family: 'TitleFont', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin-top: 24px;
}

@keyframes gradient-shift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 12px;
  gap: 2px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 6px 10px;
  border-radius: 8px;
  margin-right: 10px;
}

.user-name {
  font-weight: 500;
}

.pixels-count {
  color: var(--tg-theme-hint-color, #999999);
}

.canvas-pixels-count {
  color: var(--tg-theme-hint-color, #999999);
  font-size: 11px;
}

/* Кнопка с джойстиком в левом верхнем углу */
.game-menu-btn {
  position: absolute;
  left: 10px;
  top: calc(50% + 12px);
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.05);
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 10;
  animation: pulse 2s ease-in-out infinite;
}

.game-menu-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  transform: translateY(-50%) scale(1.1);
}

.game-menu-btn:active {
  transform: translateY(-50%) scale(0.95);
}

.game-menu-btn.active {
  background: rgba(0, 122, 255, 0.15);
  color: #007AFF;
}

@keyframes pulse {
  0%, 100% {
    transform: translateY(-50%) scale(1);
  }
  50% {
    transform: translateY(-50%) scale(1.05);
  }
}

/* Модальное окно игры */
.game-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.game-menu {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 20px;
  padding: 24px;
  max-width: 90%;
  width: 400px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.game-menu h2 {
  margin: 0 0 20px 0;
  font-size: 24px;
  text-align: center;
}

.game-menu-item {
  width: 100%;
  padding: 16px;
  margin-bottom: 12px;
  border: none;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.05);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  text-align: center;
}

.game-menu-item:hover {
  background: rgba(0, 122, 255, 0.1);
  transform: scale(1.02);
}

.game-menu-item:active {
  transform: scale(0.98);
}

.game-icon {
  font-size: 32px;
}

.game-title {
  font-size: 18px;
  font-weight: 600;
  color: #000;
}

.game-desc {
  font-size: 14px;
  color: #666;
}

.game-menu-close {
  width: 100%;
  padding: 12px;
  margin-top: 12px;
  border: none;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.1);
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.2s;
}

.game-menu-close:hover {
  background: rgba(0, 0, 0, 0.15);
}

.game-menu-close:active {
  transform: scale(0.98);
}

/* Темная тема для модального окна */
@media (prefers-color-scheme: dark) {
  .game-menu {
    background: rgba(28, 28, 30, 0.95);
    color: #ffffff;
  }
  
  .game-menu-item {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .game-menu-item:hover {
    background: rgba(0, 122, 255, 0.2);
  }
  
  .game-title {
    color: #ffffff;
  }
  
  .game-desc {
    color: #999;
  }
  
  .game-menu-close {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }
  
  .game-menu-close:hover {
    background: rgba(255, 255, 255, 0.15);
  }
}

.game-wrapper {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 100px;
}

/* Выбор цвета в header */
.header-color-picker {
  position: absolute;
  right: 10px;
  top: calc(50% + 12px);
  transform: translateY(-50%);
  z-index: 10;
}

.header-color-picker input[type="color"] {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.05);
  padding: 4px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-color-picker input[type="color"]:hover {
  transform: scale(1.1);
}

.header-color-picker input[type="color"]:active {
  transform: scale(0.95);
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #f0f0f0;
  padding-bottom: 100px; /* Отступ для bottom bar с отступами */
  padding-top: 60px; /* Отступ для header поверх контента */
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


/* iOS-style Bottom Bar - прямоугольник с закругленными углами, компактный */
.ios-bottom-bar {
  position: fixed;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 14px;
  padding-bottom: max(10px, calc(14px + env(safe-area-inset-bottom)));
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  border-radius: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1), 0 0 0 0.5px rgba(0, 0, 0, 0.05);
  z-index: 1000;
  width: fit-content;
  min-width: auto;
}

/* Темная тема для iOS bottom bar */
@media (prefers-color-scheme: dark) {
  .ios-bottom-bar {
    background: rgba(28, 28, 30, 0.7);
    border: 0.5px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 0.5px rgba(255, 255, 255, 0.05);
  }
  
  .ios-btn {
    background: rgba(255, 255, 255, 0.1);
    color: var(--tg-theme-text-color, #ffffff);
  }
  
  .ios-btn:active {
    background: rgba(255, 255, 255, 0.15);
  }
  
  .ios-btn.active {
    background: rgba(0, 122, 255, 0.25);
    color: #5AC8FA;
  }
}

.ios-bar-content {
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
  flex-wrap: nowrap;
}

.ios-btn {
  padding: 10px 14px;
  border: none;
  border-radius: 12px;
  font-size: 13px;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.05);
  color: var(--tg-theme-text-color, #000000);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 60px;
  min-width: 60px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  position: relative;
  overflow: hidden;
}

.ios-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.3s, height 0.3s;
}

.ios-btn:active::before {
  width: 200px;
  height: 200px;
}

.ios-btn:active {
  transform: scale(0.95);
  background: rgba(0, 0, 0, 0.1);
}

.ios-btn.active {
  background: rgba(0, 122, 255, 0.15);
  color: #007AFF;
}

.ios-btn.active .ios-icon {
  transform: scale(1.1);
}

.ios-icon {
  font-size: 24px;
  line-height: 1;
  display: inline-block;
  transition: transform 0.2s;
}

.ios-label {
  font-size: 11px;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
}

.ios-btn.icon-only {
  min-width: 50px;
  min-height: 50px;
  padding: 10px;
}

.ios-btn.icon-only .ios-icon {
  font-size: 20px;
}

.ios-btn.icon-only .ios-label {
  display: none;
}

/* Адаптивность для мобильных устройств */
@media (max-width: 768px) {
  .header {
    padding: 8px;
    flex-wrap: wrap;
  }

  .header h1 {
    font-size: 18px;
  }

  .user-info {
    font-size: 11px;
    width: 100%;
    margin-top: 4px;
    align-items: flex-start;
  }

  .ios-bottom-bar {
    bottom: 12px;
    padding: 8px 12px;
    padding-bottom: max(8px, calc(12px + env(safe-area-inset-bottom)));
    border-radius: 28px;
  }

  .ios-bar-content {
    gap: 6px;
  }

  .ios-btn {
    min-height: 56px;
    min-width: 56px;
    padding: 8px 12px;
  }

  .ios-btn.icon-only {
    min-width: 48px;
    min-height: 48px;
    padding: 8px;
  }

  .ios-icon {
    font-size: 22px;
  }

  .ios-label {
    font-size: 10px;
  }

  .color-picker {
    top: 5px;
    right: 5px;
    padding: 8px;
    font-size: 12px;
  }

  .color-picker input[type="color"] {
    width: 36px;
    height: 36px;
  }

  .color-hex {
    font-size: 12px;
  }
}

/* Очень маленькие экраны */
@media (max-width: 480px) {
  .header h1 {
    font-size: 16px;
  }

  .user-info {
    font-size: 10px;
  }

  .ios-bottom-bar {
    bottom: 8px;
    padding: 6px 10px;
    padding-bottom: max(6px, calc(8px + env(safe-area-inset-bottom)));
    border-radius: 26px;
  }

  .ios-bar-content {
    gap: 4px;
  }

  .ios-btn {
    min-height: 52px;
    min-width: 52px;
    padding: 6px 10px;
  }

  .ios-btn.icon-only {
    min-width: 44px;
    min-height: 44px;
    padding: 6px;
  }

  .ios-icon {
    font-size: 20px;
  }

  .ios-label {
    font-size: 9px;
  }
}
</style>
