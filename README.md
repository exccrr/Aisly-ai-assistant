# Aisly-ai-assistant

## 🚀 Возможности

- 🎙️ Запись аудио с устройства (например, BlackHole)
- 🔤 Транскрипция речи на русском через `faster-whisper`
- 🧠 Ответы от модели GROQ (`llama3-70b-8192`)
- 📜 UI с markdown, подсветкой кода и анимацией
- 📝 Редактирование текста до повторной отправки
- 💬 История запросов + исправление технических терминов
- ⌨️ Управление через горячие клавиши

## 🗂️ Структура проекта

```
aisly/
├── main.py
├── audio/
│   ├── __init__.py
│   └── recorder.py
├── groq/
│   ├── __init__.py
│   └── client.py
├── prompt/
│   ├── system.md
│   ├── legend.md
│   └── technical_terms.txt
├── ui/
│   ├── __init__.py
│   ├── floating_panel.py
│   ├── response_window.py
│   └── edit_dialog.py
├── utils/
│   ├── __init__.py
│   └── text_helpers.py
├── whisper/
│   ├── __init__.py
│   └── transcriber.py
```

## ⌨️ Горячие клавиши

| Комбинация     | Действие                   |
|----------------|----------------------------|
| `Ctrl + Enter` | Начать запись              |
| `Ctrl + L`     | Очистить историю           |
| `Meta + H`     | Скрыть интерфейс           |
| `Ctrl + H`     | Показать/скрыть ответ GPT  |

## 🧪 Установка зависимостей

Установи зависимости с помощью:

```bash
pip install -r requirements.txt
```

Пример содержимого `requirements.txt`:
```
PyQt6
httpx
sounddevice
numpy
scipy
faster-whisper
markdown
pygments
```

## 🔐 Переменные окружения

Не храни API-ключ в коде. Вместо этого:

1. Установи переменную окружения:
   ```bash
   export GROQ_API_KEY=your_token_here
   ```

2. Или создай `.env` файл:

   ```
   GROQ_API_KEY=your_token_here
   ```

   И используй `python-dotenv` для загрузки.

## ▶️ Запуск

```bash
cd aisly
python main.py
```

