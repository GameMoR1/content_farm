# local-clipper

Локальный инструмент для нарезки, транскрипции, рефрейминга и генерации клипов из видео (YouTube/файл) с офлайн-процессингом и UI.

## Быстрый старт

1. Установите ffmpeg и добавьте в PATH.
2. Создайте виртуальное окружение:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # или source .venv/bin/activate для Linux/Mac
   ```
3. Установите зависимости:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Скачайте модели whisper/spacy (и onnx при необходимости):
   ```bash
   bash backend/scripts/setup_models.sh
   ```
5. Запустите backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
6. Откройте frontend/index.html в браузере (или смонтируйте как StaticFiles).

### Для Ollama (опционально)
- Установите Ollama: https://ollama.com/
- Выполните:
  ```bash
  ollama pull qwen2.5:3b
  ```
- Укажите OLLAMA_MODEL в .env

## Структура
- `backend/` — FastAPI, сервисы, пайплайн, воркеры, тесты
- `frontend/` — HTML/CSS/JS, компоненты, стили
- `media/` — исходники, артефакты, рендеры

## Функционал
- API: запуск задач, прогресс, генерация меты, рендер
- Очередь и прогресс — asyncio, без Redis
- Кэширование по SHA1 исходника
- Полностью офлайн, без внешних API
- Поддержка моделей whisper (faster-whisper), spacy, mediapipe/YOLOv8n-face
- Генерация субтитров, стилей, эмодзи-инъекция
- Детекция хайлайтов, рефрейминг 9:16, рендер клипов

## Важно
- Не использовать Docker и внешние API
- В UI отображается предупреждение об авторских правах: ответственность на пользователе

## Скрипты
- `backend/scripts/setup_models.sh` — загрузка моделей
- `backend/scripts/demo.sh` — обработка sample.mp4 через пайплайн

## Тесты
- `backend/tests/` — unit-тесты: highlight scoring, reframing smoothness, captions export

---

**local-clipper** — полностью локальный инструмент для креаторов и исследователей видео-контента.
