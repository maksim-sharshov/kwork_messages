# Архитектура проекта kwork-bot-v2

## Обзор

Проект представляет собой Telegram бота для автоматизации управления диалогами на платформе Kwork с интеграцией GPT-4o для генерации ответов.

**Основной процесс**:
1. Получить диалоги с аккаунтов Kwork
2. Проверить новые сообщения
3. Создать топики в Telegram для каждого диалога
4. Обработать сообщения (через AI или менеджера)
5. Сохранить результаты в БД

---

## Архитектурные компоненты

### 1. KworkManager (Оркестратор)

**Файл**: `manager/kwork.py`

Главный оркестратор, управляющий основным потоком обработки диалогов.

**Ответственность**:
- Запуск циклического менеджера каждые 40 сек
- Получение диалогов для каждого аккаунта
- Проверка новых сообщений
- Делегирование обработки процессорам сообщений
- Управление флагами режима обработки

**Методы**:
- `run()` — бесконечный цикл менеджера
- `task()` — основная задача (выполняется каждые 40 сек)
- `check_messages()` — сбор непроцессированных сообщений
- `update_flag_and_check()` — управление флагами ManagerMode

---

### 2. MessageProcessor (Абстрактный процессор)

**Файл**: `services/message_processor.py`

Абстрактный базовый класс для обработки сообщений. Использует **паттерн Strategy**.

```
MessageProcessor (ABC)
├── AIMessageProcessor — обработка с помощью GPT
└── ManagerMessageProcessor — обработка менеджером (без ИИ)
```

**Интерфейс**:
- `can_process(message, account_id) -> bool` — может ли обработать это сообщение
- `process(message, kwork_account, account_id) -> None` — обработать сообщение

**AIMessageProcessor**:
- Проверяет флаг ManagerMode (если False, может обработать)
- Загружает файлы из сообщения через FileService
- Формирует контекст (текст + файлы + время работы)
- Генерирует ответ через GPTHandler
- Отправляет ответ в Kwork и Telegram
- Если есть заявка, устанавливает флаг ManagerMode в True

**ManagerMessageProcessor**:
- Обрабатывает сообщения, которые не были обработаны AI
- Загружает и отправляет файлы в Telegram
- Записывает сообщение в БД для менеджера

---

### 3. FileService (Работа с файлами)

**Файл**: `services/file_service.py`

Сервис для загрузки, парсинга и отправки файлов в Telegram.

**Методы**:
- `download_file(file_path, headers) -> (bytes, str)` — загрузить файл
- `parse_document(content, filename) -> str | None` — парсить документ
- `send_to_telegram(content, filename, chat_id, topic_id)` — отправить файл в TG
- `process_files_from_message(files_array, headers, chat_id, topic_id) -> str` — обработать все файлы из сообщения

**Использование**:
Централизованная логика работы с файлами используется обоими процессорами (AI и Manager).

---

### 4. TopicService (Управление топиками)

**Файл**: `services/topic_service.py`

Сервис для создания и управления топиками (форум-каналы) в Telegram.

**Методы**:
- `create_or_get(dialog, account) -> Chat` — создать топик или вернуть существующий
- `_format_topic_title(username, account_username) -> str` — сформировать название

**Использование**:
KworkManager вызывает `create_or_get` для каждого диалога.

---

### 5. KworkAccount (API Интеграция)

**Файл**: `integrations/kwork.py`

API клиент для платформы Kwork. Выполняет HTTP запросы к API Kwork.

**Методы**:
- `get_dialogs() -> dict` — получить список диалогов
- `get_chat_messages(user_id) -> dict | None` — получить сообщения от пользователя
- `send_message(user_id, text) -> dict` — отправить сообщение пользователю
- `get_check_notify() -> list[dict]` — проверить уведомления

**Обработка ошибок**:
Специфичные исключения вместо broad `except Exception`:
- `KworkAPIError` — ошибки API Kwork
- `asyncio.TimeoutError` — timeout
- `aiohttp.ClientError` — сетевые ошибки

---

### 6. GPTHandler (AI Интеграция)

**Файл**: `integrations/openai.py`

API клиент для OpenAI. Генерирует ответы на сообщения.

**Методы**:
- `load_prompt() -> str` — загрузить системный prompt
- `get_history() -> list[dict]` — получить историю сообщений из Redis
- `generate_response() -> (str, str | None)` — генерировать ответ GPT и извлечь заявку

**Использование**:
AIMessageProcessor вызывает `generate_response()` для каждого сообщения.

---

## Data Flow (Основной поток данных)

```
1. KworkManager.task() запускается каждые 40 сек
   ↓
2. Получить диалоги для каждого аккаунта (KworkAccount.get_dialogs)
   ↓
3. check_messages() собирает непроцессированные сообщения (KworkAccount.get_chat_messages)
   ↓
4. create_or_get() создаёт топики для новых диалогов (TopicService)
   ↓
5. Для каждого сообщения:
   ├─ Если AI может обработать (флаг ManagerMode = False):
   │  └─ AIMessageProcessor.process() (асинхронно, через asyncio.create_task)
   │     ├─ FileService.process_files_from_message()
   │     ├─ GPTHandler.generate_response()
   │     └─ KworkAccount.send_message()
   │
   └─ Если менеджер может обработать (флаг ManagerMode = True):
      └─ ManagerMessageProcessor.process() (синхронно)
         └─ FileService.process_files_from_message()
   ↓
6. Результаты сохраняются в БД (Message, MessageAI, ManagerMode)
```

---

## База данных

### PostgreSQL (основное хранилище)

**Таблицы**:
- `users` — пользователи Telegram
- `accounts` — аккаунты Kwork
- `chats` — топики (связь между диалогом Kwork и топиком Telegram)
- `messages` — сообщения (история всех сообщений)
- `manager_mode` — флаги режима обработки (AI или менеджер)

### Redis (временное хранилище)

**Модели**:
- `MessageAI` — история сообщений для контекста GPT (с TTL)

---

## Типизация

### TypedDict модели (`integrations/types.py`)

```python
class DialogDict(TypedDict):
    user_id: int
    username: str
    last_message_time: str
    unread_count: int

class MessageDict(TypedDict):
    MID: str
    mfrom: str
    MSGTO: int
    MSGFROM: int
    message: str
    filesArray: list[FileDict]
    unread: int

class GPTResponseDict(TypedDict):
    answer: str
    application: str | None
```

**Использование**: Вместо анонимных `dict`, используются структурированные TypedDict для типобезопасности.

---

## Исключения

**Файл**: `core/exceptions.py`

Иерархия исключений для явной обработки ошибок:

```
KworkBotException (базовое)
├── KworkAPIError — ошибки API Kwork
├── DatabaseError — ошибки БД
├── MessageProcessingError — ошибки обработки сообщений
├── AIProcessingError — ошибки ИИ (OpenAI)
├── FileProcessingError — ошибки обработки файлов
└── TelegramAPIError — ошибки Telegram API
```

**Преимущества**:
- Специфичные исключения вместо broad `except Exception`
- Контекст для отладки (from e)
- Возможность обработать разные типы ошибок по-разному

---

## Асинхронность и параллелизм

### Семафоры

```python
self.message_semaphore = asyncio.Semaphore(5)  # Макс 5 одновременных обработок AI
```

AIMessageProcessor использует семафор для ограничения параллельной обработки сообщений.

### create_task

```python
asyncio.create_task(self.ai_processor.process(...))  # Асинхронная обработка
```

AI обработка запускается асинхронно через `create_task`, не блокирует основной цикл.

---

## Логирование

**Loggers**:
- `manager_logger` — основные события менеджера
- `dialogs_logger` — события диалогов (JSON формат)
- `error_logger` — критические ошибки

**Использование**:
```python
logger.info("Событие")
logger.error("Ошибка", exc_info=True)
error_logger.error("Критическая ошибка")
```

---

## Конфигурация

**Файл**: `settings.py`

Использует Pydantic для управления конфигурацией:

```python
class PostgresConfig(BaseSettings):
    NAME: str
    HOST: str
    PORT: int
    PASSWORD: str
    USER: str

class GptConfig(BaseSettings):
    TOKEN: str
    MODEL: str = "gpt-4o"

class BotConfig(BaseSettings):
    TOKEN: str
    CHAT_ID: int
    COMMANDS: list[BotCommand]
```

**Переменные окружения** (`.env`):
```
BOT_TOKEN=...
BOT_CHAT_ID=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
OPENAI_TOKEN=...
```

---

## Принципы проектирования

### Single Responsibility Principle (SRP)
- KworkManager — оркестратор
- MessageProcessor — обработка сообщений
- FileService — работа с файлами
- TopicService — управление топиками
- KworkAccount — API клиент Kwork
- GPTHandler — API клиент OpenAI

### Open/Closed Principle (OCP)
- MessageProcessor абстрактный класс позволяет добавлять новые типы обработчиков без изменения KworkManager

### Dependency Inversion
- KworkManager зависит от абстракций (MessageProcessor), а не от конкретных реализаций

### Polymorphism
- AIMessageProcessor и ManagerMessageProcessor используют один интерфейс MessageProcessor

---

## Расширяемость

### Добавить новый тип обработчика

1. Создать класс, наследующий `MessageProcessor`
2. Реализовать методы `can_process()` и `process()`
3. Добавить в KworkManager.task():
   ```python
   elif await new_processor.can_process(message, account.id):
       await new_processor.process(message, account_kwork, account.id)
   ```

### Добавить новый сервис

1. Создать класс в `services/`
2. Инъектировать в KworkManager
3. Использовать в методах

---

## Тестирование

**Структура**:
```
tests/
├── conftest.py — fixtures
├── unit/
│   ├── test_model_admin.py
│   ├── test_file_service.py
│   └── test_message_processor.py
├── integration/
│   └── test_kwork_manager.py
└── fixtures/
    └── sample_messages.py
```

**Примеры**:
- Mock тесты для API интеграций
- Unit тесты для сервисов
- Integration тесты для основного потока

---

## Развёртывание

**Требования**:
- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- OpenAI API token
- Telegram Bot token
- Kwork аккаунт

**Запуск**:
```bash
pip install -r requirements.txt
python main.py
```

---

## Версионирование кода

**Последняя версия**: v2.0 (рефакторинг с ООП)
- Разделение на сервисы
- Типизация TypedDict
- Специфичные исключения
- Упрощённый KworkManager (оркестратор)

**Предыдущая версия**: v1.0 (монолитный KworkManager)
- Все методы в одном классе
- Broad exception handling
- Дублирование кода
