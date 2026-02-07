import { ref } from 'vue'
import axios from 'axios'

// Настройка axios с timeout и обработкой ошибок
const axiosInstance = axios.create({
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor для обработки ошибок сети
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message === 'Network Error' || !error.response) {
      // Ошибка сети или timeout
      const networkError = new Error('Ошибка сети. Проверьте подключение к интернету.')
      networkError.isNetworkError = true
      return Promise.reject(networkError)
    }
    return Promise.reject(error)
  }
)

export function usePixelBattle(canvasRef, containerRef) {
  const zoom = ref(1)
  const panX = ref(0)
  const panY = ref(0)
  const canvas = ref(null)
  const ctx = ref(null)
  const pixels = ref(new Map())
  const showGrid = ref(false)
  // Флаг для отладки зума
  const debugZoom = true
  // Якорь зума для стабильного поведения при серии колесиков / pinch
  let wheelAnchorActive = false
  let wheelAnchorScreen = { x: 0, y: 0 }
  let wheelAnchorWorld = { x: 0, y: 0 }
  
  const CANVAS_WIDTH = 1000
  const CANVAS_HEIGHT = 1000
  
  // Для обработки жестов тачпада
  let isPanning = false
  let lastPanPoint = { x: 0, y: 0 }
  let lastPinchDistance = 0
  let isPinching = false
  
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
  
  function redrawCanvas() {
    if (!ctx.value) return
    
    // Очищаем canvas
    ctx.value.fillStyle = '#FFFFFF'
    ctx.value.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
    
    // Рисуем все пиксели
    pixels.value.forEach((color, key) => {
      const [x, y] = key.split(',').map(Number)
      ctx.value.fillStyle = color
      ctx.value.fillRect(x, y, 1, 1)
    })
    
    // Рисуем сетку поверх, если нужно
    if (showGrid.value) {
      drawGrid()
    }
  }
  
  async function loadCanvas(apiUrl) {
    try {
      console.log(`Загрузка холста с ${apiUrl}/api/canvas/`)
      const response = await axiosInstance.get(`${apiUrl}/api/canvas/`)
      const canvasPixels = response.data
      
      console.log(`Загружено пикселей: ${canvasPixels.length}`)
      
      if (canvasPixels.length === 0) {
        console.warn('Холст пустой - пикселей нет')
      }
      
      // Очищаем canvas
      if (ctx.value) {
        ctx.value.fillStyle = '#FFFFFF'
        ctx.value.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
      }
      
      // Рисуем все пиксели
      canvasPixels.forEach((pixel, index) => {
        if (index < 10) {
          console.log(`Пиксель ${index}: x=${pixel.x}, y=${pixel.y}, color=${pixel.color}`)
        }
        drawPixel(pixel.x, pixel.y, pixel.color)
      })
      
      console.log(`Отрисовано пикселей: ${canvasPixels.length}`)
      
      // Рисуем сетку после загрузки пикселей, если нужно
      if (showGrid.value) {
        setTimeout(() => drawGrid(), 0)
      }
    } catch (error) {
      console.error('Ошибка загрузки холста:', error)
      console.error('Детали ошибки:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      })
    }
  }
  
  async function handleClick(x, y, color, apiUrl) {
    const initData = window.Telegram?.WebApp?.initData || ''
    
    try {
      const headers = {}
      if (initData) {
        headers['X-Telegram-Init-Data'] = initData
      }
      
      const response = await axiosInstance.post(
        `${apiUrl}/api/pixels/`,
        { x, y, color },
        { headers, timeout: 10000 }
      )
      
      // Рисуем пиксель сразу (оптимистичное обновление)
      drawPixel(x, y, color)
      
      return response.data
    } catch (error) {
      console.error('Ошибка размещения пикселя:', error)
      console.error('Детали ошибки:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
        isNetworkError: error.isNetworkError
      })
      
      // Обработка ошибок сети
      if (error.isNetworkError || error.code === 'ECONNABORTED' || error.message === 'Network Error') {
        throw new Error('Ошибка сети. Проверьте подключение к интернету и попробуйте снова.')
      }
      
      if (error.response?.status === 401) {
        throw new Error('Ошибка авторизации. Обновите страницу.')
      }
      
      if (error.response?.status === 422) {
        const detail = error.response?.data?.detail || 'Ошибка валидации данных'
        throw new Error(`Ошибка валидации: ${detail}`)
      }
      
      if (error.response?.status === 500) {
        throw new Error('Ошибка сервера. Попробуйте позже.')
      }
      
      const errorMessage = error.response?.data?.detail || error.message || 'Не удалось разместить пиксель'
      throw new Error(errorMessage)
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
    canvas.value.style.transform = `translate(${panX.value}px, ${panY.value}px) scale(${zoom.value})`
    canvas.value.style.transformOrigin = 'top left'
    
    // Показываем сетку при зуме > 2
    const shouldShowGrid = zoom.value > 2
    if (shouldShowGrid !== showGrid.value) {
      showGrid.value = shouldShowGrid
      redrawCanvas()
    } else if (showGrid.value) {
      redrawCanvas()
    }
  }
  
  function drawGrid() {
    if (!ctx.value || !showGrid.value) return
    
    // Сохраняем текущее состояние контекста
    ctx.value.save()
    
    const gridSize = 1 // Сетка размером 1x1 пиксель
    ctx.value.strokeStyle = 'rgba(200, 200, 200, 0.3)'
    ctx.value.lineWidth = 0.3
    
    // Рисуем сетку на всем холсте (видимость контролируется CSS transform)
    // Вертикальные линии
    for (let x = 0; x <= CANVAS_WIDTH; x += gridSize) {
      ctx.value.beginPath()
      ctx.value.moveTo(x, 0)
      ctx.value.lineTo(x, CANVAS_HEIGHT)
      ctx.value.stroke()
    }
    
    // Горизонтальные линии
    for (let y = 0; y <= CANVAS_HEIGHT; y += gridSize) {
      ctx.value.beginPath()
      ctx.value.moveTo(0, y)
      ctx.value.lineTo(CANVAS_WIDTH, y)
      ctx.value.stroke()
    }
    
    // Восстанавливаем состояние контекста
    ctx.value.restore()
  }
  
  function handleWheel(event) {
    event.preventDefault()
    
    if (!canvas.value) return
    
    const oldZoom = zoom.value
    const delta = event.deltaY > 0 ? 0.9 : 1.1
    const newZoom = Math.max(0.1, Math.min(10, oldZoom * delta))
    
    // Получаем координаты относительно контейнера (без transform)
    const container = containerRef?.value || canvas.value.parentElement
    if (!container) return
    
    const containerRect = container.getBoundingClientRect()
    const mouseX = event.clientX - containerRect.left
    const mouseY = event.clientY - containerRect.top

    // Если курсор сильно сдвинулся — переустанавливаем якорь
    const dist = Math.hypot(
      mouseX - wheelAnchorScreen.x,
      mouseY - wheelAnchorScreen.y
    )
    
    if (!wheelAnchorActive || dist > 8) {
      wheelAnchorActive = true
      wheelAnchorScreen = { x: mouseX, y: mouseY }
      // Мировые координаты: screen = pan + world * zoom => world = (screen - pan) / zoom
      wheelAnchorWorld = {
        x: (mouseX - panX.value) / oldZoom,
        y: (mouseY - panY.value) / oldZoom
      }
    }

    // Используем зафиксированные координаты якоря для стабильности
    const anchorScreenX = wheelAnchorScreen.x
    const anchorScreenY = wheelAnchorScreen.y
    const anchorWorldX = wheelAnchorWorld.x
    const anchorWorldY = wheelAnchorWorld.y

    if (debugZoom) {
      console.log('[WHEEL BEFORE]', {
        clientX: event.clientX,
        clientY: event.clientY,
        containerRect,
        mouseX,
        mouseY,
        anchorScreenX,
        anchorScreenY,
        anchorWorldX,
        anchorWorldY,
        panX: panX.value,
        panY: panY.value,
        zoom: oldZoom
      })
    }
    
    zoom.value = newZoom
    
    // Пересчитываем pan так, чтобы точка под якорем осталась на месте
    // screen = pan + world * zoom => pan = screen - world * zoom
    panX.value = anchorScreenX - anchorWorldX * newZoom
    panY.value = anchorScreenY - anchorWorldY * newZoom

    if (debugZoom) {
      console.log('[WHEEL AFTER]', {
        anchorScreenX,
        anchorScreenY,
        anchorWorldX,
        anchorWorldY,
        panX: panX.value,
        panY: panY.value,
        zoom: zoom.value
      })
    }
    
    updateCanvasTransform()
  }
  
  function handleTouchStart(event, panModeEnabled = false) {
    // Если не в режиме перемещения, не обрабатываем жесты
    if (!panModeEnabled) {
      return
    }
    
    if (event.touches.length === 1) {
      // Начало панорамирования
      isPanning = true
      lastPanPoint = { x: event.touches[0].clientX, y: event.touches[0].clientY }
    } else if (event.touches.length === 2) {
      // Начало pinch-to-zoom
      isPinching = true
      const touch1 = event.touches[0]
      const touch2 = event.touches[1]
      lastPinchDistance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      )
    }
  }
  
  function handleTouchMove(event, panModeEnabled = false) {
    if (!panModeEnabled) {
      return
    }
    
    event.preventDefault()
    
    if (isPanning && event.touches.length === 1) {
      // Панорамирование
      const currentX = event.touches[0].clientX
      const currentY = event.touches[0].clientY
      
      panX.value += currentX - lastPanPoint.x
      panY.value += currentY - lastPanPoint.y
      
      lastPanPoint = { x: currentX, y: currentY }
      updateCanvasTransform()
    } else if (isPinching && event.touches.length === 2) {
      // Pinch-to-zoom с сохранением точки под пальцами (как в картах)
      const touch1 = event.touches[0]
      const touch2 = event.touches[1]
      const distance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      )

      if (!canvas.value || lastPinchDistance === 0) {
        lastPinchDistance = distance
        return
      }

      const oldZoom = zoom.value
      const scale = distance / lastPinchDistance
      const newZoom = Math.max(0.1, Math.min(10, oldZoom * scale))

      // Центр жеста между двумя пальцами в координатах viewport
      const centerClientX = (touch1.clientX + touch2.clientX) / 2
      const centerClientY = (touch1.clientY + touch2.clientY) / 2

      // Переходим в координаты контейнера (без transform)
      const container = containerRef?.value || canvas.value.parentElement
      if (!container) {
        lastPinchDistance = distance
        return
      }
      
      const containerRect = container.getBoundingClientRect()
      const centerX = centerClientX - containerRect.left
      const centerY = centerClientY - containerRect.top

      // Мировые координаты точки под пальцами (до изменения zoom)
      // screen = pan + world * zoom => world = (screen - pan) / zoom
      const worldX = (centerX - panX.value) / oldZoom
      const worldY = (centerY - panY.value) / oldZoom

      if (debugZoom) {
        console.log('[PINCH BEFORE]', {
          touch1: { x: touch1.clientX, y: touch1.clientY },
          touch2: { x: touch2.clientX, y: touch2.clientY },
          centerClientX,
          centerClientY,
          containerRect,
          centerX,
          centerY,
          worldX,
          worldY,
          panX: panX.value,
          panY: panY.value,
          zoom: oldZoom,
          distance,
          lastPinchDistance
        })
      }

      // Обновляем zoom
      zoom.value = newZoom

      // Пересчитываем pan так, чтобы центр жеста остался на месте
      // screen = pan + world * zoom => pan = screen - world * zoom
      panX.value = centerX - worldX * newZoom
      panY.value = centerY - worldY * newZoom

      if (debugZoom) {
        console.log('[PINCH AFTER]', {
          centerX,
          centerY,
          worldX,
          worldY,
          panX: panX.value,
          panY: panY.value,
          zoom: zoom.value
        })
      }

      lastPinchDistance = distance
      updateCanvasTransform()
    }
  }
  
  function handleTouchEnd(event) {
    isPanning = false
    isPinching = false
  }
  
  function resetPan() {
    panX.value = 0
    panY.value = 0
    updateCanvasTransform()
  }
  
  return {
    initCanvas,
    drawPixel,
    loadCanvas,
    handleClick,
    zoom,
    panX,
    panY,
    resetZoom,
    zoomIn,
    zoomOut,
    resetPan,
    handleWheel,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    pixels,
    showGrid,
    updateCanvasTransform,
    redrawCanvas
  }
}
