/**
 * Composable для управления аудио
 */
import { ref } from 'vue'

const backgroundMusic = ref(null)
const soundEffects = ref({})
const isMusicEnabled = ref(true)
const isSoundEnabled = ref(true)
const musicVolume = ref(0.3) // 30% громкость для фоновой музыки
const soundVolume = ref(0.5) // 50% громкость для звуков

export function useAudio() {
  /**
   * Инициализация аудио
   */
  function initAudio() {
    try {
      // Фоновая музыка
      backgroundMusic.value = new Audio('/sounds/background-music.mp3')
      backgroundMusic.value.loop = true
      backgroundMusic.value.volume = musicVolume.value
      
      // Обработка ошибок загрузки музыки
      backgroundMusic.value.addEventListener('error', (e) => {
        console.log('Фоновая музыка не найдена. Добавьте файл /sounds/background-music.mp3')
        backgroundMusic.value = null
      })
    } catch (error) {
      console.log('Не удалось инициализировать фоновую музыку:', error)
      backgroundMusic.value = null
    }
    
    try {
      // Звуки эффектов (необязательные)
      soundEffects.value = {
        pixelPlace: new Audio('/sounds/pixel-place.mp3'),
        pixelError: new Audio('/sounds/pixel-error.mp3'),
        achievement: new Audio('/sounds/achievement.mp3'),
        notification: new Audio('/sounds/notification.mp3')
      }
      
      // Устанавливаем громкость для всех звуков
      Object.values(soundEffects.value).forEach(sound => {
        sound.volume = soundVolume.value
        // Обработка ошибок для каждого звука
        sound.addEventListener('error', () => {
          // Игнорируем ошибки - звуки необязательны
        })
      })
    } catch (error) {
      console.log('Не удалось инициализировать звуки эффектов:', error)
      soundEffects.value = {}
    }
    
    // Автовоспроизведение музыки (если включено и файл доступен)
    if (isMusicEnabled.value && backgroundMusic.value) {
      playBackgroundMusic()
    }
  }
  
  /**
   * Воспроизведение фоновой музыки
   */
  function playBackgroundMusic() {
    if (!backgroundMusic.value || !isMusicEnabled.value) return
    
    backgroundMusic.value.play().catch(error => {
      console.log('Автовоспроизведение музыки заблокировано:', error)
      // Пользователь должен взаимодействовать с интерфейсом
    })
  }
  
  /**
   * Остановка фоновой музыки
   */
  function stopBackgroundMusic() {
    if (backgroundMusic.value) {
      backgroundMusic.value.pause()
      backgroundMusic.value.currentTime = 0
    }
  }
  
  /**
   * Переключение музыки
   */
  function toggleMusic() {
    isMusicEnabled.value = !isMusicEnabled.value
    if (isMusicEnabled.value) {
      playBackgroundMusic()
    } else {
      stopBackgroundMusic()
    }
  }
  
  /**
   * Воспроизведение звука размещения пикселя
   */
  function playPixelPlaceSound() {
    if (!isSoundEnabled.value || !soundEffects.value.pixelPlace) return
    
    // Создаем новый экземпляр для возможности одновременного воспроизведения
    const sound = soundEffects.value.pixelPlace.cloneNode()
    sound.volume = soundVolume.value
    sound.play().catch(() => {
      // Игнорируем ошибки автовоспроизведения
    })
  }
  
  /**
   * Воспроизведение звука ошибки
   */
  function playErrorSound() {
    if (!isSoundEnabled.value || !soundEffects.value.pixelError) return
    
    const sound = soundEffects.value.pixelError.cloneNode()
    sound.volume = soundVolume.value
    sound.play().catch(() => {})
  }
  
  /**
   * Воспроизведение звука достижения
   */
  function playAchievementSound() {
    if (!isSoundEnabled.value || !soundEffects.value.achievement) return
    
    const sound = soundEffects.value.achievement.cloneNode()
    sound.volume = soundVolume.value
    sound.play().catch(() => {})
  }
  
  /**
   * Воспроизведение звука уведомления
   */
  function playNotificationSound() {
    if (!isSoundEnabled.value || !soundEffects.value.notification) return
    
    const sound = soundEffects.value.notification.cloneNode()
    sound.volume = soundVolume.value
    sound.play().catch(() => {})
  }
  
  /**
   * Установка громкости музыки
   */
  function setMusicVolume(volume) {
    musicVolume.value = Math.max(0, Math.min(1, volume))
    if (backgroundMusic.value) {
      backgroundMusic.value.volume = musicVolume.value
    }
  }
  
  /**
   * Установка громкости звуков
   */
  function setSoundVolume(volume) {
    soundVolume.value = Math.max(0, Math.min(1, volume))
    Object.values(soundEffects.value).forEach(sound => {
      sound.volume = soundVolume.value
    })
  }
  
  /**
   * Очистка ресурсов
   */
  function cleanup() {
    stopBackgroundMusic()
    if (backgroundMusic.value) {
      backgroundMusic.value = null
    }
    Object.values(soundEffects.value).forEach(sound => {
      sound.pause()
      sound.src = ''
    })
    soundEffects.value = {}
  }
  
  return {
    isMusicEnabled,
    isSoundEnabled,
    musicVolume,
    soundVolume,
    initAudio,
    playBackgroundMusic,
    stopBackgroundMusic,
    toggleMusic,
    playPixelPlaceSound,
    playErrorSound,
    playAchievementSound,
    playNotificationSound,
    setMusicVolume,
    setSoundVolume,
    cleanup
  }
}
