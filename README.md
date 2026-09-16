# Система интеграции платформы Kwork и Telegram с использованием искусственного интеллекта

Комплексная асинхронная система автоматизации обработки клиентских обращений, обеспечивающая двустороннюю интеграцию фриланс-платформы **Kwork** и мессенджера **Telegram**, дополненная интеллектуальным модулем на базе языковой модели (ИИ) для автоматического ведения переговоров на начальном этапе.

Проект разработан в рамках курсовой работы по дисциплине «Объектно-ориентированное программирование» студентом группы ФТ24ВР62ПИ **Шаршовым Максимом Александровичем** (Приднестровский государственный университет им. Т.Г. Шевченко).

---

## 🚀 Основные возможности

- **Многоаккаунтность Kwork:** Поддержка одновременного обслуживания нескольких аккаунтов исполнителя через хранение cookie-сессий в базе данных PostgreSQL.
- **Периодический опрос (Polling):** Независимый асинхронный опрос каждого аккаунта с настраиваемым интервалом и обработкой сетевых сбоев/таймаутов.
- **Изолированные топики Telegram:** Автоматическое создание персональных топиков в Telegram-группе для каждого нового клиента Kwork.
- **Двусторонняя синхронизация:**
  - Доставка входящих сообщений и файлов с Kwork в соответствующий Telegram-топик.
  - Отправка ответов оператора из Telegram-топика обратно на платформу Kwork от имени нужного аккаунта.
- **ИИ-ассистент начального этапа:**
  - Автоматическая генерация первичных ответов клиентам с помощью языковой модели.
  - Управление контекстом диалога и контроль лимита токенов.
  - Автоматическое определение маркера согласия клиента с условиями сотрудничества.
  - Плавная передача диалога живому оператору после подтверждения заказа с деактивацией автоответчика.
- **Гибкая система выборки данных:** Репозитории с поддержкой сложных фильтров по идентификаторам клиентов, аккаунтам, состояниям диалогов, наличию непрочитанных сообщений, времени последней активности и типам сообщений.
- **Событийная архитектура и отказоустойчивость:** Слабосвязанные модули на основе событий (`OnNewMessage`, `OnStateChanged`, `OnSessionExpired`), защита от дублирования сообщений по уникальным хешам, обработка истечения cookie-сессий (код 401) с уведомлением администратора.

---

## 🛠 Технологический стек

- **Язык программирования:** Python 3.11+
- **Асинхронность:** `asyncio`
- **Telegram API:** `aiogram`
- **HTTP-клиент:** `httpx` (с поддержкой cookie-авторизации и заголовков браузера)
- **База данных:** PostgreSQL (`asyncpg`)
- **Архитектурные паттерны:** ООП, Репозиторий (`Repository<T>`), Конечный автомат состояний (`DialogState`), Событийная модель (Observer/Publisher).

---

## 📁 Структура проекта

```text
├─── bot
│   ├─── filters
│   │   ├─── __init__.py
│   │   ├─── admin.py
│   │   └─── chat.py
│   ├─── handlers
│   │   ├─── __init__.py
│   │   ├─── group.py
│   │   └─── private.py
│   ├─── templates
│   │   ├─── __init__.py
│   │   └─── commands.py
│   └─── __init__.py
├─── core
│   ├─── __init__.py
│   ├─── bot.py
│   ├─── database.py
│   ├─── exceptions.py
│   ├─── logger.py
│   └─── redis.py
├─── data
│   └─── prompt.txt
├─── db
│   ├─── psql
│   │   ├─── crud
│   │   │   ├─── __init__.py
│   │   │   └─── base.py
│   │   ├─── models
│   │   │   ├─── __init__.py
│   │   │   ├─── enum.py
│   │   │   ├─── mapped_columns.py
│   │   │   └─── models.py
│   │   └─── __init__.py
│   ├─── redis
│   │   ├─── models
│   │   │   ├─── __init__.py
│   │   │   ├─── mapped_columns.py
│   │   │   └─── models.py
│   │   └─── __init__.py
│   └─── __init__.py
├─── docs
│   ├─── AI_HANDLERS_ARCHITECTURE.md
│   ├─── ARCHITECTURE.md
│   ├─── FINAL_CHECKLIST.md
│   ├─── QUICK_START.md
│   └─── TESTING.md
├─── integrations
│   ├─── ai
│   │   ├─── __init__.py
│   │   ├─── application_parser.py
│   │   ├─── base.py
│   │   ├─── factory.py
│   │   ├─── gemini.py
│   │   ├─── gpt.py
│   │   └─── history_manager.py
│   ├─── __init__.py
│   ├─── kwork.py
│   ├─── templates.py
│   └─── types.py
├─── logs
│   ├─── .gitkeep
│   ├─── dialogs.json
│   ├─── error.log
│   ├─── logs.log
│   ├─── manager.log
│   └─── notification_loger.log
├─── manager
│   ├─── __init__.py
│   ├─── base.py
│   └─── kwork.py
├─── services
│   ├─── file_service.py
│   ├─── message_processor.py
│   ├─── report_timer.py
│   └─── topic_service.py
├─── tests
│   ├─── unit
│   │   ├─── __init__.py
│   │   ├─── test_file_service.py
│   │   └─── test_message_processor.py
│   ├─── __init__.py
│   └─── conftest.py
├─── utils
│   ├─── .DS_Store
│   ├─── __init__.py
│   ├─── kwork.py
│   └─── time.py
├─── .env
├─── .gitignore
├─── README
├─── README.md
├─── bot.dockerfile
├─── cookie-documentation.png
├─── docker-compose.yml
├─── main.py
├─── manager.dockerfile
├─── manager.py
├─── requirements.txt
└─── settings.py
```

---

## 📐 Архитектура и проектирование

Система спроектирована по строгим принципам объектно-ориентированного программирования с разделением ответственности между слоями:
1. **Интерфейсный и абстрактный слои (`IEntity`, `BaseEntity`, `BasePoller`):** Устраняют дублирование инфраструктурной логики, стандартизируют свойства сущностей и управление жизненным циклом фоновых задач.
2. **Слой данных (`Repository<T>`):** Обобщенный репозиторий реализует стандартные CRUD-операции, а специализированные наследники предоставляют мощные методы динамической фильтрации (`get_by_filters`).
3. **Интеграционные адаптеры (`KworkClient`, `TelegramAdapter`):** Инкапсулируют всю специфику взаимодействия с внешними API (Kwork и Telegram).
4. **Бизнес-логика и оркестрация (`MessageRouter`, `AIModule`):** Управляют потоками сообщений, состоянием диалогов конечного автомата (`AI_ACTIVE`, `OPERATOR_ACTIVE`, `WAITING`) и взаимодействием с LLM.

---

## ⚙️ Установка и запуск

### Требования

- **Python 3.11+** (Docker-образы собираются на `python:3.12-slim`)
- **PostgreSQL 12+**
- **Redis 6+**
- Токен Telegram-бота и ID форум-группы (супергруппы с включёнными топиками)
- Cookie аккаунта Kwork (как получить — см. `cookie-documentation.png`)
- API-ключ OpenAI и/или Google Gemini

---

### Вариант A. Запуск через Docker (рекомендуется)

`docker-compose.yml` поднимает сразу весь стек: PostgreSQL, Redis, Telegram-бота и менеджера Kwork.

**1. Клонирование репозитория**
```bash
git clone <repo-url>
cd kwork-bot-v2
```

**2. Создание файла `.env`** (см. раздел «Настройка окружения» ниже). Для Docker дополнительно укажите пароль суперпользователя PostgreSQL:
```env
POSTGRES_PASSWORD=your_postgres_password
```
> Внутри Docker-сети хосты БД и Redis — это имена сервисов: `POSTGRES_HOST=postgres`, `REDIS_HOST=redis`. Их нужно прописать в `.env` для контейнеров (либо оставить локальные значения при запуске без Docker).

**3. Сборка и запуск**
```bash
docker compose up --build
```

Будут запущены контейнеры:
- `postgres` — база данных;
- `redis` — хранилище контекста ИИ;
- `bot` — Telegram-бот (`main.py`);
- `manager` — менеджер Kwork (`manager.py`).

Остановка:
```bash
docker compose down          # остановить
docker compose down -v       # остановить и удалить тома с данными
```

---

### Вариант B. Локальный запуск

**1. Клонирование репозитория**
```bash
git clone <repo-url>
cd kwork-bot-v2
```

**2. Виртуальное окружение**
```bash
python -m venv venv
source venv/bin/activate     # Linux/macOS
# venv\Scripts\activate      # Windows
```

**3. Установка зависимостей**
```bash
pip install -r requirements.txt
```

**4. Настройка окружения** — создайте файл `.env` в корне проекта (см. раздел ниже).

**5. Инфраструктура** — запустите PostgreSQL и Redis (локально или в Docker):
```bash
docker compose up -d postgres redis
```

**6. Добавление аккаунта Kwork** — после первого запуска таблицы создаются автоматически. Вставьте cookie аккаунта в таблицу `accounts`:
```sql
INSERT INTO accounts (cookie) VALUES ('<строка cookie с kwork.ru>');
```
Поле `username` заполнится автоматически при первом опросе аккаунта менеджером.

**7. Запуск приложения** — система состоит из двух независимых процессов, запускать их нужно **в отдельных терминалах**:

```bash
python main.py       # Telegram-бот: приём команд и пересылка ответов оператора в Kwork
python manager.py    # Менеджер Kwork: опрос диалогов, создание топиков, запуск ИИ
```

---

### Настройка окружения (`.env`)

Все переменные читаются через `pydantic-settings` в `settings.py`. Имена переменных задаются префиксами соответствующих конфигов.

```env
# --- Telegram Bot (префикс BOT_) ---
BOT_TOKEN=123456:AA...              # токен бота от @BotFather
BOT_CHAT_ID=-1001234567890          # ID форум-группы (с топиками)

# --- PostgreSQL (префикс POSTGRES_) ---
POSTGRES_NAME=my_db
POSTGRES_HOST=localhost             # в Docker: postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# --- Redis (префикс REDIS_) ---
REDIS_NAME=0
REDIS_HOST=localhost                # в Docker: redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# --- LLM (необязательно, хотя бы один провайдер) ---
OPENAI_TOKEN=sk-...                 # ключ OpenAI (префикс OPENAI_)
OPENAI_GPT_ENABLED=true
GEMINI_TOKEN=AIza...                # ключ Google Gemini (префикс GEMINI_)
GEMINI_GMN_ENABLED=true
```

> ⚠️ Файл `.env` добавлен в `.gitignore` — никогда не коммитьте реальные токены, cookie и пароли.

---

## 🧪 Тестирование

Проект включает модульные, интеграционные и системные тесты с использованием `pytest`:
```bash
pytest tests/
```
Проверяются сценарии:
- Корректность парсинга и обработки сетевых ошибок / истёкших сессий Kwork.
- Атомарность операций репозитория и отсутствие дубликатов сообщений.
- Корректность обрезания контекста токенов и определения маркера согласия ИИ-модулем.
- Двусторонняя маршрутизация через Telegram-топики.
