# ToDo Bot & Backend Service

![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)
![Build Status](https://img.shields.io/github/actions/workflow/status/EdvardFarrow/todo_bot/tests.yml?branch=main)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.0-green)

[English](#english) | [Русский](#russian)

---

<a name="english"></a>
## English

A full-stack task management service. Includes a Django REST API backend and an async Telegram Bot (Aiogram), all wrapped in Docker.

### Key Architectural Decisions

1.  **Snowflake ID Generator:**
    * Used **Twitter Snowflake** (`int64`) instead of standard auto-increment or UUIDs.
    * Unlike UUIDs, Snowflake IDs are sortable by time, which keeps PostgreSQL B-Tree indexes efficient and fast.

2.  **Timezone Handling:**
    * **Backend:** Defaults to `America/Adak` (UTC-10), but stores everything in UTC.
    * **Bot:** Automatically detects the user's timezone (via location or profile) and converts deadlines to local time before displaying them. No more mental math for the user.

3.  **Context-Aware Voice Input:**
    * The bot uses **Google Gemini** to transcribe voice notes.
    * It understands context: if you are in the "New Task" menu, the voice note becomes the task title. If you are managing categories, it becomes the category name.

4.  **Tech Stack:**
    * **Backend:** Django 5, DRF, PostgreSQL, Redis, Celery (Beat & Worker).
    * **Bot:** Aiogram 3.10, Aiogram-Dialog, Aiohttp.
    * **Infra:** Docker Compose, uv (fast package manager), GitHub Actions (CI).

### How to Run

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/EdvardFarrow/todo_bot.git
    cd todo_bot
    ```

2.  **Setup Environment:**
    Create a `.env` file in the root directory:
    ```env
    BOT_TOKEN=your_telegram_bot_token
    GEMINI_API_KEY=your_gemini_api_key
    SECRET_KEY=django_secret_key
    ```

3.  **Run with Docker:**
    ```bash
    docker compose up --build
    ```
    * Backend API: `http://localhost:8000/api/v1/`
    * Admin Panel: `http://localhost:8000/admin/`

---

<a name="russian"></a>
## Русский

Сервис для управления задачами. Состоит из Django REST API (бэкенд) и асинхронного Telegram-бота. Всё упаковано в Docker.

### Архитектурные решения

1.  **Snowflake ID Generator:**
    * Вместо стандартных `id` или `UUID` реализован алгоритм **Twitter Snowflake** (64-битные числа).
    * Такие ID уникальны в распределенной системе, но при этом сортируются по времени. Это намного полезнее для индексов базы данных (PostgreSQL), чем рандомные UUID.

2.  **Работа с часовыми поясами:**
    * **Backend:** Настроен на зону `America/Adak`. В БД всё хранится строго в UTC.
    * **Bot:** Бот сам определяет часовой пояс пользователя (через локацию или настройки) и при отображении конвертирует время в локальное.

3.  **Голосовое управление (AI):**
    * Подключен **Google Gemini Flash**. Бот переводит голосовые в текст и понимает контекст: если вы в меню создания задачи — текст станет заголовком; если в меню категорий — названием категории.

4.  **Инфраструктура и качество:**
    * Настроен CI через **GitHub Actions**.
    * Написаны тесты (pytest) с покрытием кода **97%**.
    * Используется `uv` для очень быстрой сборки Docker-образов.

### Запуск

1.  **Клонируем репозиторий:**
    ```bash
    git clone https://github.com/EdvardFarrow/todo_bot.git
    cd todo_bot
    ```

2.  **Настраиваем переменные:**
    Создайте файл `.env` в корне проекта:
    ```env
    BOT_TOKEN=ваш_токен_бота
    GEMINI_API_KEY=ваш_ключ_gemini
    SECRET_KEY=django_секретный_ключ
    ```

3.  **Запускаем:**
    ```bash
    docker compose up --build
    ```
    * Backend API: `http://localhost:8000/api/v1/`
    * Admin Panel: `http://localhost:8000/admin/`