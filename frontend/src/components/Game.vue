<template>
  <div class="game-container">
    <div class="game-header">
      <h2>🎮 Повтори пиксели</h2>
      <div class="game-info">
        <span>Уровень: {{ currentLevel }}</span>
        <span>Поле: {{ gridSize }}x{{ gridSize }}</span>
      </div>
    </div>

    <!-- Меню выбора режима -->
    <div v-if="gameStatus === 'idle'" class="game-menu">
      <button @click="startSoloGame" class="game-btn primary">
        🎯 Одиночная игра
      </button>
      <button @click="showPvPMenu = true" class="game-btn secondary">
        👥 PvP игра
      </button>
      <button @click="openLeaderboard" class="game-btn">
        🏆 Лидерборд
      </button>
    </div>

    <!-- PvP меню -->
    <div v-if="showPvPMenu" class="pvp-menu">
      <button @click="createPvPGame" class="game-btn primary">
        Создать игру
      </button>
      <div class="join-section">
        <input 
          v-model="joinCode" 
          placeholder="Код игры" 
          class="code-input"
          @keyup.enter="joinPvPGame"
        />
        <button @click="joinPvPGame" class="game-btn">
          Присоединиться
        </button>
      </div>
      <button @click="showPvPMenu = false" class="game-btn">
        Назад
      </button>
    </div>

    <!-- Игровое поле -->
    <div v-if="gameStatus === 'playing'" class="game-board">
      <div 
        class="grid" 
        :class="`grid-${gridSize}`"
      >
        <div
          v-for="(row, y) in gridSize"
          :key="`row-${y}`"
          class="grid-row"
        >
          <div
            v-for="(col, x) in gridSize"
            :key="`cell-${x}-${y}`"
            class="grid-cell"
            :class="{
              'highlighted': isCellHighlighted(x, y),
              'clicked': isCellClicked(x, y),
              'disabled': isShowingSequence || !isWaitingForInput
            }"
            @click="handleCellClick(x, y)"
          ></div>
        </div>
      </div>

      <div class="game-status">
        <div v-if="isShowingSequence" class="status-message">
          Смотри внимательно...
        </div>
        <div v-else-if="isWaitingForInput" class="status-message">
          Повтори последовательность
        </div>
        <div v-else class="status-message">
          Готовься...
        </div>
      </div>
    </div>

    <!-- Результат игры -->
    <div v-if="gameStatus === 'finished'" class="game-result">
      <h3>Игра окончена!</h3>
      <p>Достигнутый уровень: {{ finalLevel }}</p>
      <button @click="resetGame" class="game-btn primary">
        Играть снова
      </button>
    </div>

    <!-- Лидерборд -->
    <div v-if="showLeaderboard" class="leaderboard">
      <h3>🏆 Лидерборд</h3>
      <div class="leaderboard-list">
        <div 
          v-for="(entry, index) in leaderboard" 
          :key="entry.user_id"
          class="leaderboard-entry"
        >
          <span class="rank">#{{ index + 1 }}</span>
          <span class="name">{{ entry.name }}</span>
          <span class="level">Уровень {{ entry.max_level }}</span>
        </div>
      </div>
      <button @click="showLeaderboard = false" class="game-btn">
        Закрыть
      </button>
    </div>

    <!-- Ошибка -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useGame } from '../composables/useGame'

const props = defineProps({
  user: {
    type: Object,
    default: null
  }
})

const {
  game,
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
  resetGame: resetGameComposable,
  connectGameWebSocket,
  disconnectGameWebSocket,
  onGameMessage
} = useGame()

const showPvPMenu = ref(false)
const showLeaderboard = ref(false)
const joinCode = ref('')
const leaderboard = ref([])
const finalLevel = ref(1)
const highlightedCell = ref(null)
const clickedCells = ref(new Set())

// Получить ID пользователя
function getUserId() {
  // Используем telegram_id из user объекта (если есть)
  if (props.user?.telegram_id) {
    return props.user.telegram_id
  }
  // Fallback: из Telegram WebApp
  if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
    return window.Telegram.WebApp.initDataUnsafe.user.id
  }
  // Fallback для разработки
  return 1
}

async function startSoloGame() {
  try {
    await createGame('solo')
    await startLevel()
  } catch (err) {
    console.error('Ошибка создания игры:', err)
  }
}

async function createPvPGame() {
  try {
    const gameData = await createGame('pvp')
    // Подключаемся к WebSocket
    const telegramId = getUserId()
    connectGameWebSocket(gameData.id, telegramId)
    
    // Показываем код для приглашения
    alert(`Код игры: ${gameData.code}\n\nПоделись этим кодом с другом!`)
    
    // Ждём подключения второго игрока через WebSocket
    const unsubscribe = onGameMessage((message) => {
      if (message.type === 'player_connected') {
        // Второй игрок подключился, начинаем игру
        startLevel()
        unsubscribe()
      }
    })
  } catch (err) {
    console.error('Ошибка создания PvP игры:', err)
  }
}

async function joinPvPGame() {
  if (!joinCode.value) {
    alert('Введите код игры')
    return
  }
  
  try {
    const gameData = await joinGame(joinCode.value.toUpperCase())
    // Подключаемся к WebSocket
    const telegramId = getUserId()
    connectGameWebSocket(gameData.id, telegramId)
    
    // Уведомляем, что готовы
    // Игра начнётся автоматически, когда оба игрока будут готовы
    
    await startLevel()
  } catch (err) {
    console.error('Ошибка присоединения к игре:', err)
    alert('Не удалось присоединиться к игре. Проверьте код.')
  }
}

async function startLevel() {
  if (!sequence.value || sequence.value.length === 0) {
    return
  }
  
  // Показываем последовательность
  await showSequenceWithAnimation(sequence.value, 1000)
  
  // Ждём ввода от пользователя
  isWaitingForInput.value = true
  userSequence.value = []
  clickedCells.value.clear()
}

async function showSequenceWithAnimation(seq, delayMs) {
  isShowingSequence.value = true
  
  for (let i = 0; i < seq.length; i++) {
    const cell = seq[i]
    highlightedCell.value = `${cell.x}-${cell.y}`
    
    await new Promise(resolve => setTimeout(resolve, delayMs))
    
    highlightedCell.value = null
    await new Promise(resolve => setTimeout(resolve, 200))
  }
  
  isShowingSequence.value = false
}

function handleCellClick(x, y) {
  if (isShowingSequence.value || !isWaitingForInput.value) {
    return
  }
  
  addToUserSequence(x, y)
  clickedCells.value.add(`${x}-${y}`)
  
  // Убираем подсветку через 300ms
  setTimeout(() => {
    clickedCells.value.delete(`${x}-${y}`)
  }, 300)
  
  // Проверяем, завершена ли последовательность
  if (userSequence.value.length === sequence.value.length) {
    checkAnswer()
  }
}

async function checkAnswer() {
  isWaitingForInput.value = false
  
  try {
    const result = await submitAnswer(userSequence.value)
    
    if (result.correct) {
      // Правильно - следующий уровень
      await new Promise(resolve => setTimeout(resolve, 1000))
      await startLevel()
    } else {
      // Неправильно - игра окончена
      finalLevel.value = result.levelReached
      gameStatus.value = 'finished'
      
      // Сохраняем результат
      await finishGame(
        result.levelReached,
        result.levelReached, // correct_answers
        1, // errors
        null // play_time_seconds (можно добавить отслеживание)
      )
    }
  } catch (err) {
    console.error('Ошибка проверки ответа:', err)
  }
}

function isCellHighlighted(x, y) {
  return highlightedCell.value === `${x}-${y}`
}

function isCellClicked(x, y) {
  return clickedCells.value.has(`${x}-${y}`)
}

async function loadLeaderboard() {
  try {
    leaderboard.value = await getLeaderboard(10)
  } catch (err) {
    console.error('Ошибка загрузки лидерборда:', err)
  }
}

function resetGame() {
  resetGameComposable()
  showPvPMenu.value = false
  showLeaderboard.value = false
  joinCode.value = ''
}

onMounted(() => {
  // Можно загрузить лидерборд заранее
  // loadLeaderboard()
})

// Загружаем лидерборд при открытии
async function openLeaderboard() {
  showLeaderboard.value = true
  await loadLeaderboard()
}

onUnmounted(() => {
  disconnectGameWebSocket()
})
</script>

<style scoped>
.game-container {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.game-header {
  text-align: center;
  margin-bottom: 20px;
}

.game-header h2 {
  margin: 0 0 10px 0;
}

.game-info {
  display: flex;
  justify-content: center;
  gap: 20px;
  font-size: 14px;
  color: #666;
}

.game-menu,
.pvp-menu {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.game-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.game-btn.primary {
  background: #007AFF;
  color: white;
}

.game-btn.primary:hover {
  background: #0056CC;
}

.game-btn.secondary {
  background: #34C759;
  color: white;
}

.game-btn.secondary:hover {
  background: #28A745;
}

.join-section {
  display: flex;
  gap: 10px;
}

.code-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  text-transform: uppercase;
}

.game-board {
  margin: 20px 0;
}

.grid {
  display: inline-block;
  border: 2px solid #333;
  border-radius: 8px;
  padding: 10px;
  background: #f5f5f5;
}

.grid-row {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
}

.grid-row:last-child {
  margin-bottom: 0;
}

.grid-cell {
  width: 60px;
  height: 60px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.grid-4 .grid-cell {
  width: 50px;
  height: 50px;
}

.grid-5 .grid-cell {
  width: 40px;
  height: 40px;
}

.grid-cell:hover:not(.disabled) {
  border-color: #007AFF;
  transform: scale(1.05);
}

.grid-cell.highlighted {
  background: #34C759;
  border-color: #28A745;
  transform: scale(1.1);
}

.grid-cell.clicked {
  background: #007AFF;
  border-color: #0056CC;
}

.grid-cell.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.game-status {
  text-align: center;
  margin-top: 20px;
  font-size: 18px;
  font-weight: bold;
}

.status-message {
  color: #666;
}

.game-result {
  text-align: center;
  padding: 40px 20px;
}

.game-result h3 {
  margin-bottom: 20px;
}

.leaderboard {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
}

.leaderboard h3 {
  margin-top: 0;
  text-align: center;
}

.leaderboard-list {
  margin: 20px 0;
}

.leaderboard-entry {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  margin-bottom: 8px;
  background: white;
  border-radius: 4px;
}

.leaderboard-entry .rank {
  font-weight: bold;
  color: #007AFF;
}

.leaderboard-entry .name {
  flex: 1;
  margin-left: 10px;
}

.leaderboard-entry .level {
  color: #666;
}

.error-message {
  background: #FF3B30;
  color: white;
  padding: 12px;
  border-radius: 8px;
  margin-top: 20px;
  text-align: center;
}
</style>
