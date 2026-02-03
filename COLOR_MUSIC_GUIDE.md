# Музыка на основе цветов - Руководство по реализации

## 🎵 Концепция

**Идея**: Каждый цвет = нота/звук. Когда игрок размещает пиксель, играет соответствующая нота. Из последовательности пикселей создается мелодия.

## 🔧 Как это работает (без датасетов!)

### Подход 1: Маппинг цветов в ноты (Рекомендуется)

**Принцип**: 
- HEX цвет → RGB → частота звука
- Каждый цветной канал (R, G, B) влияет на параметры звука
- Используем Web Audio API для генерации звуков программно

**Преимущества**:
- ✅ Не нужны датасеты
- ✅ Работает в браузере
- ✅ Полный контроль над звуком
- ✅ Легко настраивается

### Подход 2: Цвет → MIDI нота

**Принцип**:
- Маппинг цветов в MIDI ноты (0-127)
- Использование готовых синтезаторов
- Более "музыкальный" результат

### Подход 3: Гармонические последовательности

**Принцип**:
- Группировка похожих цветов в аккорды
- Создание гармоничных последовательностей
- Более сложная, но красивая музыка

---

## 🎹 Маппинг цветов в звуки

### Вариант A: Простой маппинг (RGB → Частота)

```javascript
// Красный канал → основная частота
// Зеленый канал → тембр/обертоны
// Синий канал → длительность/громкость

function colorToFrequency(color) {
  const r = parseInt(color.slice(1, 3), 16) // 0-255
  const g = parseInt(color.slice(3, 5), 16)
  const b = parseInt(color.slice(5, 7), 16)
  
  // Маппинг в музыкальный диапазон (C4 = 261.63 Hz до C6 = 1046.5 Hz)
  const minFreq = 261.63  // C4
  const maxFreq = 1046.5  // C6
  const frequency = minFreq + (r / 255) * (maxFreq - minFreq)
  
  return frequency
}
```

### Вариант B: Маппинг в ноты хроматической гаммы

```javascript
// 12 нот в октаве × несколько октав
const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
const OCTAVES = [3, 4, 5, 6] // 4 октавы

function colorToNote(color) {
  const r = parseInt(color.slice(1, 3), 16)
  const g = parseInt(color.slice(3, 5), 16)
  
  const noteIndex = r % 12
  const octaveIndex = Math.floor(g / 64) % 4
  
  return {
    note: NOTES[noteIndex],
    octave: OCTAVES[octaveIndex],
    frequency: noteToFrequency(NOTES[noteIndex], OCTAVES[octaveIndex])
  }
}
```

### Вариант C: Маппинг в пентатонику (более гармонично)

```javascript
// Пентатоника - всегда звучит гармонично
const PENTATONIC = ['C', 'D', 'E', 'G', 'A'] // 5 нот

function colorToPentatonicNote(color) {
  const r = parseInt(color.slice(1, 3), 16)
  const noteIndex = r % 5
  const octave = 4 + Math.floor(r / 51) // 4-6 октавы
  
  return {
    note: PENTATONIC[noteIndex],
    octave: octave,
    frequency: noteToFrequency(PENTATONIC[noteIndex], octave)
  }
}
```

---

## 🎛️ Web Audio API - Генерация звуков

### Базовый синтезатор

```javascript
class ColorSynth {
  constructor() {
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
    this.oscillators = new Map() // Для одновременных звуков
  }
  
  // Генерация тона из цвета
  playColor(color, duration = 0.2) {
    const frequency = this.colorToFrequency(color)
    const oscillator = this.audioContext.createOscillator()
    const gainNode = this.audioContext.createGain()
    
    // Подключение
    oscillator.connect(gainNode)
    gainNode.connect(this.audioContext.destination)
    
    // Настройка
    oscillator.frequency.value = frequency
    oscillator.type = 'sine' // или 'triangle', 'sawtooth', 'square'
    
    // Огибающая (envelope) для плавного звука
    const now = this.audioContext.currentTime
    gainNode.gain.setValueAtTime(0, now)
    gainNode.gain.linearRampToValueAtTime(0.3, now + 0.01) // Attack
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration) // Decay
    
    // Воспроизведение
    oscillator.start(now)
    oscillator.stop(now + duration)
  }
  
  colorToFrequency(color) {
    const r = parseInt(color.slice(1, 3), 16)
    const minFreq = 261.63  // C4
    const maxFreq = 1046.5  // C6
    return minFreq + (r / 255) * (maxFreq - minFreq)
  }
}
```

### Продвинутый синтезатор с эффектами

```javascript
class AdvancedColorSynth {
  constructor() {
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
    this.masterGain = this.audioContext.createGain()
    this.masterGain.connect(this.audioContext.destination)
    this.masterGain.gain.value = 0.3 // Общая громкость
  }
  
  playColor(color, x, y) {
    const { frequency, type, duration } = this.colorToSoundParams(color, x, y)
    
    // Осциллятор
    const oscillator = this.audioContext.createOscillator()
    oscillator.frequency.value = frequency
    oscillator.type = type
    
    // Gain для огибающей
    const gainNode = this.audioContext.createGain()
    
    // Фильтр (на основе зеленого канала)
    const filter = this.audioContext.createBiquadFilter()
    filter.type = 'lowpass'
    const g = parseInt(color.slice(3, 5), 16)
    filter.frequency.value = 200 + (g / 255) * 8000
    
    // Эффект реверберации (опционально)
    const convolver = this.createReverb()
    
    // Подключение цепочки
    oscillator.connect(filter)
    filter.connect(gainNode)
    if (convolver) {
      gainNode.connect(convolver)
      convolver.connect(this.masterGain)
    } else {
      gainNode.connect(this.masterGain)
    }
    
    // Огибающая
    const now = this.audioContext.currentTime
    gainNode.gain.setValueAtTime(0, now)
    gainNode.gain.linearRampToValueAtTime(0.5, now + 0.01)
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration)
    
    oscillator.start(now)
    oscillator.stop(now + duration)
  }
  
  colorToSoundParams(color, x, y) {
    const r = parseInt(color.slice(1, 3), 16)
    const g = parseInt(color.slice(3, 5), 16)
    const b = parseInt(color.slice(5, 7), 16)
    
    // Частота из красного канала
    const minFreq = 220  // A3
    const maxFreq = 880  // A5
    const frequency = minFreq + (r / 255) * (maxFreq - minFreq)
    
    // Тип волны из зеленого канала
    const types = ['sine', 'triangle', 'sawtooth', 'square']
    const type = types[Math.floor(g / 64) % 4]
    
    // Длительность из синего канала
    const duration = 0.1 + (b / 255) * 0.4 // 0.1 - 0.5 секунды
    
    return { frequency, type, duration }
  }
  
  createReverb() {
    // Простая реверберация (можно упростить или убрать)
    return null
  }
}
```

---

## 🎼 Создание мелодии из последовательности

### Вариант 1: Простое воспроизведение

```javascript
class ColorMelody {
  constructor() {
    this.synth = new ColorSynth()
    this.sequence = [] // История цветов
    this.isPlaying = false
  }
  
  addPixel(color, x, y) {
    // Добавляем в последовательность
    this.sequence.push({ color, x, y, timestamp: Date.now() })
    
    // Воспроизводим сразу
    this.synth.playColor(color)
    
    // Ограничиваем размер последовательности
    if (this.sequence.length > 100) {
      this.sequence.shift()
    }
  }
  
  // Воспроизведение всей последовательности
  async playSequence() {
    if (this.isPlaying) return
    this.isPlaying = true
    
    for (const pixel of this.sequence) {
      this.synth.playColor(pixel.color)
      await this.sleep(200) // Пауза между нотами
    }
    
    this.isPlaying = false
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}
```

### Вариант 2: Гармонизация (аккорды)

```javascript
class HarmonizedColorMelody {
  constructor() {
    this.synth = new ColorSynth()
    this.recentColors = [] // Последние N цветов
    this.maxRecent = 5
  }
  
  addPixel(color, x, y) {
    this.recentColors.push(color)
    if (this.recentColors.length > this.maxRecent) {
      this.recentColors.shift()
    }
    
    // Воспроизводим аккорд из последних цветов
    this.playChord(this.recentColors)
  }
  
  playChord(colors) {
    // Воспроизводим все цвета одновременно (аккорд)
    colors.forEach(color => {
      this.synth.playColor(color, 0.3)
    })
  }
}
```

---

## 📚 Ресурсы (без датасетов!)

### Web Audio API документация:
- [MDN Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Web Audio API Tutorial](https://www.html5rocks.com/en/tutorials/webaudio/intro/)

### Музыкальная теория:
- **Ноты и частоты**: C4 = 261.63 Hz, A4 = 440 Hz (стандарт)
- **Пентатоника**: Всегда звучит гармонично
- **Хроматическая гамма**: 12 нот в октаве

### Готовые библиотеки (опционально):
- **Tone.js** - Продвинутый синтезатор для веба
- **Pizzicato.js** - Простой синтезатор
- **Howler.js** - Аудио библиотека

---

## 🚀 Быстрая реализация

**Не нужно**:
- ❌ Датасеты
- ❌ Обучение моделей
- ❌ Внешние API (кроме опциональных эффектов)

**Нужно**:
- ✅ Web Audio API (встроен в браузер)
- ✅ Маппинг цветов в частоты
- ✅ Простой синтезатор

**Время реализации**: 2-4 часа для базовой версии

---

## 💡 Идеи для улучшения

1. **Ритм**: Синий канал определяет ритм (длительность паузы)
2. **Тембр**: Зеленый канал меняет тип волны
3. **Громкость**: Яркость цвета влияет на громкость
4. **Эффекты**: Реверберация, дилей, хорус
5. **Запись**: Сохранение мелодии как WAV файл
6. **Визуализация**: Визуализация звуковых волн

---

## 🎯 Рекомендация

**Начните с простого**:
1. Маппинг RGB → частота (красный канал)
2. Простой синтезатор (sine wave)
3. Воспроизведение при размещении пикселя

**Потом добавьте**:
- Разные типы волн
- Эффекты
- Гармонизацию
- Запись мелодии

**Не нужно**:
- Сложные датасеты
- Обучение моделей
- Внешние сервисы (для базовой версии)
