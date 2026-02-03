import { ref } from 'vue'
import axios from 'axios'

export function usePixelBattle(canvasRef) {
  const zoom = ref(1)
  const canvas = ref(null)
  const ctx = ref(null)
  const pixels = ref(new Map())
  
  const CANVAS_WIDTH = 1000
  const CANVAS_HEIGHT = 1000
  
  async function initCanvas() {
    if (!canvasRef.value) return
    
    canvas.value = canvasRef.value
    ctx.value = canvas.value.getContext('2d')
    
    // Устанавливаем размер canvas
    const dpr = window.devicePixelRatio || 1
    const rect = canvas.value.getBoundingClientRect()
    
    canvas.value.width = CANVAS_WIDTH * dpr
    canvas.value.height = CANVAS_HEIGHT * dpr
    
    canvas.value.style.width = `${CANVAS_WIDTH}px`
    canvas.value.style.height = `${CANVAS_HEIGHT}px`
    
    ctx.value.scale(dpr, dpr)
    
    // Очищаем canvas
    ctx.value.fillStyle = '#FFFFFF'
    ctx.value.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
  }
  
  function drawPixel(x, y, color) {
    if (!ctx.value) return
    
    ctx.value.fillStyle = color
    ctx.value.fillRect(x, y, 1, 1)
    
    // Сохраняем пиксель в карте
    const key = `${x},${y}`
    pixels.value.set(key, color)
  }
  
  async function loadCanvas(apiUrl) {
    try {
      const response = await axios.get(`${apiUrl}/api/canvas/`)
      const canvasPixels = response.data
      
      // Очищаем canvas
      if (ctx.value) {
        ctx.value.fillStyle = '#FFFFFF'
        ctx.value.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
      }
      
      // Рисуем все пиксели
      canvasPixels.forEach(pixel => {
        drawPixel(pixel.x, pixel.y, pixel.color)
      })
    } catch (error) {
      console.error('Ошибка загрузки холста:', error)
    }
  }
  
  async function handleClick(x, y, color, apiUrl) {
    const initData = window.Telegram?.WebApp?.initData || ''
    
    try {
      const response = await axios.post(
        `${apiUrl}/api/pixels/`,
        { x, y, color },
        {
          headers: {
            'X-Telegram-Init-Data': initData
          }
        }
      )
      
      // Рисуем пиксель сразу (оптимистичное обновление)
      drawPixel(x, y, color)
      
      return response.data
    } catch (error) {
      if (error.response?.status === 429) {
        throw new Error('Кулдаун не истёк. Подождите немного.')
      }
      throw error
    }
  }
  
  function zoomIn() {
    zoom.value = Math.min(zoom.value * 1.2, 10)
    updateCanvasTransform()
  }
  
  function zoomOut() {
    zoom.value = Math.max(zoom.value / 1.2, 0.1)
    updateCanvasTransform()
  }
  
  function resetZoom() {
    zoom.value = 1
    updateCanvasTransform()
  }
  
  function updateCanvasTransform() {
    if (!canvas.value) return
    canvas.value.style.transform = `scale(${zoom.value})`
    canvas.value.style.transformOrigin = 'top left'
  }
  
  return {
    initCanvas,
    drawPixel,
    loadCanvas,
    handleClick,
    zoom,
    resetZoom,
    zoomIn,
    zoomOut
  }
}
