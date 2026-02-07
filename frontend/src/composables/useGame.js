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
  const gameStatus = ref('idle') // idle, playing, finished
  const error = ref(null)
  
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
      currentLevel.value = response.data.current_level
      gridSize.value = response.data.grid_size
      sequence.value = response.data.sequence || []
      gameStatus.value = 'playing'
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
      currentLevel.value = response.data.current_level
      gridSize.value = response.data.grid_size
      sequence.value = response.data.sequence || []
      gameStatus.value = 'playing'
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
    createGame,
    joinGame,
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
