# Шрифты

Поместите ваши файлы шрифтов в эту папку.

## Поддерживаемые форматы:
- `.woff2` (рекомендуется - лучшая сжатость)
- `.woff`
- `.ttf`
- `.otf`

## Пример структуры:
```
fonts/
  ├── YourFont-Regular.woff2
  ├── YourFont-Bold.woff2
  └── YourFont-Italic.woff2
```

## После добавления файлов:
1. Укажите имя вашего шрифта в `App.vue` в классе `.gradient-text`
2. Обновите `@font-face` правила в `App.vue` или `style.css`
