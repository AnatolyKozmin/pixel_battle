<template>
  <div class="app">
    <div class="header">
      <h1>🎨 Pixel Battle</h1>
      <div class="user-info">
        <span v-if="user">{{ user.first_name || 'Пользователь' }}</span>
        <span class="pixels-count">Пикселей: {{ user?.pixels_placed || 0 }}</span>
      </div>
    </div>
    
    <div class="canvas-container">
      <canvas
        ref="canvasRef"
        @click="handleCanvasClick"
        @mousemove="handleMouseMove"
        @mouseleave="handleMouseLeave"
      ></canvas>
      
      <div v-if="selectedColor" class="color-picker">
        <input
          type="color"
          v-model="selectedColor"
          @change="updateColor"
        />
        <span class="color-hex">{{ selectedColor }}</span>
      </div>
      
      <div v-if="cooldown > 0" class="cooldown-overlay">
        <div class="cooldown-text">Кулдаун: {{ cooldown }}с</div>
      </div>
    </div>
    
    <div class="controls">
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
const cooldown = ref(0)
const user = ref(null)

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

const { 
  initCanvas, 
  drawPixel, 
  loadCanvas, 
  handleClick,
  zoom,
  resetZoom,
  zoomIn: zoomInCanvas,
  zoomOut: zoomOutCanvas
} = usePixelBattle(canvasRef)

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
  
  // Подключение WebSocket
  connect()
  onPixelUpdate((data) => {
    drawPixel(data.x, data.y, data.color)
  })
  
  // Загрузка информации о пользователе
  await loadUserInfo()
  
  // Инициализация аудио
  initAudio()
})

onUnmounted(() => {
  disconnect()
  cleanupAudio()
})

async function loadUserInfo() {
  try {
    const initData = window.Telegram?.WebApp?.initData || ''
    const response = await fetch(`${API_URL}/api/users/me`, {
      headers: {
        'X-Telegram-Init-Data': initData
      }
    })
    if (response.ok) {
      user.value = await response.json()
    }
  } catch (error) {
    console.error('Ошибка загрузки пользователя:', error)
  }
}

async function handleCanvasClick(event) {
  if (cooldown.value > 0) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = Math.floor((event.clientX - rect.left) / zoom.value)
  const y = Math.floor((event.clientY - rect.top) / zoom.value)
  
  try {
    await handleClick(x, y, selectedColor.value, API_URL)
    playPixelPlaceSound() // Звук успешного размещения
    cooldown.value = 5 // 5 секунд кулдаун
    const interval = setInterval(() => {
      cooldown.value--
      if (cooldown.value <= 0) {
        clearInterval(interval)
      }
    }, 1000)
  } catch (error) {
    console.error('Ошибка размещения пикселя:', error)
    playErrorSound() // Звук ошибки
    alert('Не удалось разместить пиксель. Попробуйте позже.')
  }
}

function handleMouseMove(event) {
  // Можно добавить предпросмотр пикселя
}

function handleMouseLeave() {
  // Скрыть предпросмотр
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

.cooldown-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.cooldown-text {
  background: rgba(255, 255, 255, 0.9);
  padding: 20px 40px;
  border-radius: 8px;
  font-size: 24px;
  font-weight: bold;
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
