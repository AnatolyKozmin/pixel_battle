import { ref } from 'vue'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002'

export function useGame() {
  const game = ref(null)
  const gameWs = ref(null)
  const isConnected = ref(false)
  const currentLevel = ref(1)
  const gridSize = ref(3)
  const sequence = ref([])
  const userSequence = ref([])
  const isShowingSequence = ref(false)
  const isWaitingForInput = ref(false)
  const gameStatus = ref('idle') // idle, playing, finished, waiting_queue
  const error = ref(null)
  
  // Для PvP режима
  const pixelsToPlace = ref(5)
  const pixelsPlaced = ref(0)
  const opponentPixels = ref([]) // Пиксели оппонента в порядке размещения
  const myPixels = ref([]) // Мои пиксели
  const isInQueue = ref(false)
  const winnerId = ref(null)
  
  const wsListeners = []
  
  function connectGameWebSocket(gameId, telegramId) {
    if (gameWs.value?.readyState === WebSocket.OPEN) {
      return
    }
    
    const wsUrl = API_URL.replace('http://', 'ws://').replace('https://', 'wss://')
    const url = `${wsUrl}/ws/game/${gameId}?telegram_id=${telegramId}`
    
    try {
      gameWs.value = new WebSocket(url)
      
      gameWs.value.onopen = () => {
        console.log('Game WebSocket connected')
        isConnected.value = true
      }
      
      gameWs.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          wsListeners.forEach(listener => listener(data))
        } catch (error) {
          console.error('Ошибка парсинга WebSocket сообщения:', error)
        }
      }
      
      gameWs.value.onerror = (error) => {
        console.error('Game WebSocket error:', error)
        isConnected.value = false
      }
      
      gameWs.value.onclose = () => {
        console.log('Game WebSocket disconnected')
        isConnected.value = false
      }
    } catch (error) {
      console.error('Ошибка подключения Game WebSocket:', error)
    }
  }
  
  function disconnectGameWebSocket() {
    if (gameWs.value) {
      gameWs.value.close()
      gameWs.value = null
      isConnected.value = false
    }
  }
  
  function onGameMessage(callback) {
    wsListeners.push(callback)
    return () => {
      const index = wsListeners.indexOf(callback)
      if (index > -1) {
        wsListeners.splice(index, 1)
      }
    }
  }
  
  function sendGameMessage(message) {
    if (gameWs.value?.readyState === WebSocket.OPEN) {
      gameWs.value.send(JSON.stringify(message))
    }
  }
  
  async function createGame(mode = 'solo') {
    try {
      const initData = window.Telegram?.WebApp?.initData || ''
      const headers = {}
      if (initData) {
        headers['X-Telegram-Init-Data'] = initData
      }
      
      const response = await axios.post(
        `${API_URL}/api/games/create`,
        { mode },
        { headers }
      )
      
      game.value = response.data
      
      // Для SOLO режима
      if (response.data.mode === 'solo') {
        currentLevel.value = response.data.current_level
        gridSize.value = response.data.grid_size
        sequence.value = response.data.sequence || []
        gameStatus.value = 'playing'
      }
      // Для PvP режима
      else if (response.data.mode === 'pvp') {
        gridSize.value = response.data.grid_size || 10
        pixelsToPlace.value = response.data.pixels_to_place || 5
        
        // Определяем, кто мы (player1 или player2) по current_user_id
        const currentUserId = response.data.current_user_id
        const isPlayer1 = response.data.player1_id === currentUserId
        
        if (isPlayer1) {
          myPixels.value = response.data.player1_pixels || []
          opponentPixels.value = response.data.player2_pixels || []
        } else {
          myPixels.value = response.data.player2_pixels || []
          opponentPixels.value = response.data.player1_pixels || []
        }
        
        pixelsPlaced.value = myPixels.value.length
        
        if (response.data.status === 'waiting') {
          gameStatus.value = 'waiting'
        } else {
          gameStatus.value = 'playing'
        }
      }
      
      error.value = null
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }
  
  async function joinGame(code) {
    try {
      const initData = window.Telegram?.WebApp?.initData || ''
      const headers = {}
      if (initData) {
        headers['X-Telegram-Init-Data'] = initData
      }
      
      const response = await axios.post(
        `${API_URL}/api/games/join`,
        { code },
        { headers }
      )
      
      game.value = response.data
      
      // Для PvP режима
      if (response.data.mode === 'pvp') {
        gridSize.value = response.data.grid_size || 10
        pixelsToPlace.value = response.data.pixels_to_place || 5
        
        // Определяем, кто мы (player1 или player2) по current_user_id
        const currentUserId = response.data.current_user_id
        const isPlayer1 = response.data.player1_id === currentUserId
        
        if (isPlayer1) {
          myPixels.value = response.data.player1_pixels || []
          opponentPixels.value = response.data.player2_pixels || []
        } else {
          myPixels.value = response.data.player2_pixels || []
          opponentPixels.value = response.data.player1_pixels || []
        }
        
        pixelsPlaced.value = myPixels.value.length
        gameStatus.value = 'playing'
        
        // Подключаемся к WebSocket
        const telegramId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 1
        connectGameWebSocket(response.data.id, telegramId)
      } else {
        currentLevel.value = response.data.current_level
        gridSize.value = response.data.grid_size
        sequence.value = response.data.sequence || []
        gameStatus.value = 'playing'
      }
      
      error.value = null
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }
  
  async function submitAnswer(answerSequence) {
    if (!game.value) {
      throw new Error('Игра не создана')
    }
    
    try {
      const initData = window.Telegram?.WebApp?.initData || ''
      const headers = {}
      if (initData) {
        headers['X-Telegram-Init-Data'] = initData
      }
      
      const response = await axios.post(
        `${API_URL}/api/games/${game.value.id}/answer`,
        { sequence: answerSequence },
        { headers }
      )
      
      if (response.data.correct) {
        // Правильный ответ - переход на следующий уровень
        currentLevel.value = response.data.next_level
        gridSize.value = response.data.grid_size
        sequence.value = response.data.sequence
        userSequence.value = []
        return { correct: true, nextLevel: response.data.next_level }
      } else {
        // Неправильный ответ - игра окончена
        gameStatus.value = 'finished'
        return { correct: false, levelReached: response.data.level_reached }
      }
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }
  
  async function finishGame(levelReached, correctAnswers, errors, playTimeSeconds) {
    if (!game.value) {
      return
    }
    
    try {
      const initData = window.Telegram?.WebApp?.initData || ''
      const headers = {}
      if (initData) {
        headers['X-Telegram-Init-Data'] = initData
      }
      
      const response = await axios.post(
        `${API_URL}/api/games/${game.value.id}/finish`,
        null,
        {
          params: {
            level_reached: levelReached,
            correct_answers: correctAnswers,
            errors: errors,
            play_time_seconds: playTimeSeconds
          },
          headers
        }
      )
      
      return response.data
    } catch (err) {
      console.error('Ошибка при завершении игры:', err)
    }
  }
  
  async function getLeaderboard(limit = 10) {
    try {
      const response = await axios.get(
        `${API_URL}/api/games/leaderboard`,
        { params: { limit } }
      )
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }
  
  function showSequence(seq, delayMs = 1000) {
    return new Promise((resolve) => {
      isShowingSequence.value = true
      userSequence.value = []
      
      let index = 0
      const interval = setInterval(() => {
        if (index < seq.length) {
          // Подсвечиваем ячейку
          const cell = seq[index]
          // Эмитируем событие для подсветки (будет обработано в компоненте)
          index++
        } else {
          clearInterval(interval)
          isShowingSequence.value = false
          isWaitingForInput.value = true
          resolve()
        }
      }, delayMs)
    })
  }
  
  function addToUserSequence(x, y) {
    if (!isWaitingForInput.value) {
      return
    }
    
    userSequence.value.push({ x, y })
  }
  
  async function joinQueue() {
    try {
      const initData = window.Telegram?.WebApp?.initData || ''
      const headers = {}
      if (initData) {
        headers['X-Telegram-Init-Data'] = initData
      }
      
      const response = await axios.post(
        `${API_URL}/api/games/queue`,
        {},
        { headers }
      )
      
      if (response.data.status === 'matched') {
        // Нашли пару, игра создана
        game.value = response.data.game
        gridSize.value = response.data.game.grid_size || 10
        pixelsToPlace.value = response.data.game.pixels_to_place || 5
        
        // Определяем, кто мы (player1 или player2) по current_user_id из ответа
        const currentUserId = response.data.current_user_id
        const isPlayer1 = response.data.game.player1_id === currentUserId
        
        if (isPlayer1) {
          myPixels.value = response.data.game.player1_pixels || []
          opponentPixels.value = response.data.game.player2_pixels || []
        } else {
          myPixels.value = response.data.game.player2_pixels || []
          opponentPixels.value = response.data.game.player1_pixels || []
        }
        
        pixelsPlaced.value = myPixels.value.length
        gameStatus.value = 'playing'
        isInQueue.value = false
        
        // Подключаемся к WebSocket
        const telegramId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 1
        connectGameWebSocket(response.data.game.id, telegramId)
        
        return { matched: true, game: response.data.game, current_user_id: currentUserId }
      } else {
        // В очереди, ждём пару
        isInQueue.value = true
        gameStatus.value = 'waiting_queue'
        return { matched: false, waiting: true }
      }
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }
  
  async function leaveQueue() {
    try {
      const initData = window.Telegram?.WebApp?.initData || ''
      const headers = {}
      if (initData) {
        headers['X-Telegram-Init-Data'] = initData
      }
      
      await axios.post(
        `${API_URL}/api/games/queue/leave`,
        {},
        { headers }
      )
      
      isInQueue.value = false
      gameStatus.value = 'idle'
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }
  
  async function placePixel(x, y, color) {
    if (!game.value) {
      throw new Error('Игра не создана')
    }
    
    try {
      const initData = window.Telegram?.WebApp?.initData || ''
      const headers = {}
      if (initData) {
        headers['X-Telegram-Init-Data'] = initData
      }
      
      const response = await axios.post(
        `${API_URL}/api/games/${game.value.id}/place-pixel`,
        { x, y, color },
        { headers }
      )
      
      // Обновляем состояние
      pixelsPlaced.value = response.data.pixels_placed
      
      // Добавляем пиксель в список
      myPixels.value.push({ x, y, color, timestamp: Date.now() })
      
      // Отправляем через WebSocket оппоненту
      sendGameMessage({
        type: 'pixel_placed',
        x,
        y,
        color,
        timestamp: Date.now(),
        pixels_placed: response.data.pixels_placed,
        pixels_remaining: response.data.pixels_remaining
      })
      
      // Проверяем, завершена ли игра
      if (response.data.game_finished) {
        gameStatus.value = 'finished'
        winnerId.value = response.data.winner_id
        
        // Уведомляем оппонента
        sendGameMessage({
          type: 'game_finished',
          winner_id: response.data.winner_id
        })
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }
  
  function resetGame() {
    game.value = null
    currentLevel.value = 1
    gridSize.value = 3
    sequence.value = []
    userSequence.value = []
    isShowingSequence.value = false
    isWaitingForInput.value = false
    gameStatus.value = 'idle'
    error.value = null
    pixelsToPlace.value = 5
    pixelsPlaced.value = 0
    opponentPixels.value = []
    myPixels.value = []
    isInQueue.value = false
    winnerId.value = null
    disconnectGameWebSocket()
  }
  
  return {
    game,
    isConnected,
    currentLevel,
    gridSize,
    sequence,
    userSequence,
    isShowingSequence,
    isWaitingForInput,
    gameStatus,
    error,
    // PvP режим
    pixelsToPlace,
    pixelsPlaced,
    opponentPixels,
    myPixels,
    isInQueue,
    winnerId,
    // Методы
    createGame,
    joinGame,
    joinQueue,
    leaveQueue,
    placePixel,
    submitAnswer,
    finishGame,
    getLeaderboard,
    showSequence,
    addToUserSequence,
    resetGame,
    connectGameWebSocket,
    disconnectGameWebSocket,
    onGameMessage,
    sendGameMessage
  }
}
