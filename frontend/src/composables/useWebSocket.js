export function useWebSocket(url) {
  let ws = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 5
  const listeners = []
  
  function connect() {
    if (ws?.readyState === WebSocket.OPEN) return
    
    try {
      ws = new WebSocket(url + '/ws')
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        reconnectAttempts = 0
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          listeners.forEach(listener => listener(data))
        } catch (error) {
          console.error('Ошибка парсинга WebSocket сообщения:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
        // Попытка переподключения
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          setTimeout(() => {
            console.log(`Попытка переподключения ${reconnectAttempts}...`)
            connect()
          }, 1000 * reconnectAttempts)
        }
      }
    } catch (error) {
      console.error('Ошибка подключения WebSocket:', error)
    }
  }
  
  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
  }
  
  function onPixelUpdate(callback) {
    listeners.push(callback)
    
    // Возвращаем функцию для отписки
    return () => {
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }
  
  return {
    connect,
    disconnect,
    onPixelUpdate
  }
}
