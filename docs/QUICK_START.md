# 🚀 QUICK START: Первые шаги с проектом

## За 5 минут

### 1. Клонировать и установить
```bash
git clone <repo>
cd kwork-bot-v2
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

### 2. Запустить тесты
```bash
pytest tests/unit/ -v
```

**Ожидаемо**: 15 тестов должны пройти ✅

### 3. Прочитать документацию
- **Архитектура**: `docs/ARCHITECTURE.md`
- **Как писать тесты**: `TESTING.md`
- **Что было сделано**: `FINAL_CHECKLIST.md`

---

## За 15 минут

### Структура проекта

```
kwork-bot-v2/
├── core/                      # Ядро
│   ├── bot.py                # Telegram Bot объект
│   ├── database.py           # SQLAlchemy setup
│   ├── exceptions.py         # ✨ Пользовательские исключения
│   └── logger.py             # Логирование
│
├── manager/                   # Менеджеры
│   ├── base.py               # Абстрактный класс
│   └── kwork.py              # ✨ Упрощённый оркестратор (160 строк)
│
├── services/                  # ✨ Новые сервисы (разделение ответственности)
│   ├── file_service.py       # Работа с файлами
│   ├── message_processor.py  # Strategy pattern для обработки сообщений
│   └── topic_service.py      # Управление топиками
│
├── integrations/              # Интеграции
│   ├── kwork.py              # API Kwork ✨ (специфичные исключения)
│   ├── openai.py             # API OpenAI
│   └── types.py              # ✨ TypedDict модели
│
├── db/                        # База данных
│   ├── psql/                 # PostgreSQL
│   │   └── models/
│   │       └── models.py     # ✨ Типизация get()
│   └── redis/                # Redis
│
├── bot/                       # Telegram Bot handlers
├── utils/                     # Утилиты
├── settings.py               # Конфигурация
├── main.py                   # Точка входа
│
├── tests/                     # ✨ Тесты (15 работающих)
│   ├── conftest.py           # Fixtures
│   └── unit/
│       ├── test_file_service.py       # 8 тестов
│       └── test_message_processor.py  # 7 тестов
│
└── docs/                      # Документация
    ├── ARCHITECTURE.md       # ✨ Полная архитектура
    ├── TESTING.md            # ✨ Тестирование
    ├── REFACTORING_SUMMARY.md
    ├── TESTS_FIXES.md
    ├── FINAL_CHECKLIST.md
    └── (этот файл)
```

**✨** = новое или изменённое в рефакторинге

---

## Основные компоненты

### 1. KworkManager (manager/kwork.py)
**Что делает**: Оркестрирует основной процесс
- Получает диалоги с Kwork
- Проверяет новые сообщения
- Создаёт топики в Telegram
- Делегирует обработку процессорам

```python
async def task(self):
    for account in accounts:
        dialogs = await kwork_account.get_dialogs()
        messages = await self.check_messages(dialogs, kwork_account)
        
        for message in messages:
            if await self.ai_processor.can_process(message, account.id):
                asyncio.create_task(...)  # AI обработка
            elif await self.manager_processor.can_process(message, account.id):
                await self.manager_processor.process(...)  # Менеджер обработка
```

### 2. MessageProcessor (services/message_processor.py)
**Что делает**: Обрабатывает сообщения

**AI версия**: Генерирует ответ через GPT  
**Manager версия**: Просто отправляет в Telegram менеджеру

### 3. FileService (services/file_service.py)
**Что делает**: Загружает, парсит и отправляет файлы

```python
await FileService.process_files_from_message(
    files_array,
    headers,
    chat_id,
    topic_id
)
```

### 4. Исключения (core/exceptions.py)
**Вместо**: broad `except Exception`  
**Используем**: специфичные исключения

```python
try:
    await kwork_account.send_message(...)
except KworkAPIError as e:
    logger.error(f"Ошибка API: {e}")
except DatabaseError as e:
    logger.error(f"Ошибка БД: {e}")
```

---

## Шпаргалка по тестам

### Запустить
```bash
# Все тесты
pytest

# Только файл
pytest tests/unit/test_file_service.py -v

# Конкретный тест
pytest tests/unit/test_file_service.py::test_download_file_success -v

# С логами
pytest -v -s

# С покрытием
pytest --cov=services --cov=manager --cov-report=html
```

### Написать новый тест
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_something():
    """Описание теста"""
    with patch('module.SomeClass') as mock:
        mock.method = AsyncMock(return_value="result")
        
        result = await my_async_function()
        
        assert result == "expected"
        mock.method.assert_called_once()
```

---

## Принципы ООП в этом проекте

### ✅ Наследование
```python
class KworkManager(BaseManager):  # Наследует от BaseManager
    async def run(self):
        pass  # Реализует абстрактный метод
```

### ✅ Полиморфизм (Strategy)
```python
class MessageProcessor(ABC):
    @abstractmethod
    async def process(self, message): pass

class AIMessageProcessor(MessageProcessor):
    async def process(self, message): ...  # Своя реализация

class ManagerMessageProcessor(MessageProcessor):
    async def process(self, message): ...  # Другая реализация
```

### ✅ Инкапсуляция
```python
class FileService:
    @staticmethod
    def _extract_data(content):  # Приватный метод
        return data
    
    @staticmethod
    async def download_file(url):  # Публичный метод
        return _extract_data(...)
```

### ✅ Абстракция
```python
# Вся сложность скрыта:
document_text = await FileService.process_files_from_message(
    files_array,
    headers,
    chat_id,
    topic_id
)
# Внутри: загрузка, парсинг, отправка, обработка ошибок
```

---

## Если что-то не работает

### Проблема: ImportError
**Решение**: 
```bash
pip install -r requirements.txt
```

### Проблема: Тесты не запускаются
**Решение**: 
```bash
pip install pytest pytest-asyncio
pytest --version  # Проверить версию
```

### Проблема: Асинхронные тесты зависают
**Решение**: Проверить `event_loop` fixture в conftest.py

### Проблема: Mock не работает
**Решение**: Использовать `AsyncMock` для async методов
```python
# ❌ Не работает
mock.method.return_value = value

# ✅ Работает
mock.method = AsyncMock(return_value=value)
```

---

## Что дальше?

### Для разработчика
1. Прочитать `docs/ARCHITECTURE.md`
2. Запустить `pytest` и посмотреть тесты
3. Изменить код и проверить что тесты всё ещё проходят
4. Если нужна новая функция → написать тест → реализовать

### Для тех. лида
1. Посмотреть `FINAL_CHECKLIST.md`
2. Запустить full check: `mypy && pytest && pylint`
3. Встроить в CI/CD (GitHub Actions, GitLab CI)
4. Добавить требование к покрытию (например, 80%)

### Для QA
1. Посмотреть `TESTING.md`
2. Запустить тесты: `pytest -v`
3. Добавить свои integration/E2E тесты
4. Проверить код через `pytest --cov`

---

## Ссылки на документацию

- **Архитектура**: `docs/ARCHITECTURE.md`
- **Тестирование**: `TESTING.md`
- **Рефакторинг ООП**: `REFACTORING_SUMMARY.md`
- **Что было исправлено в тестах**: `TESTS_FIXES.md`
- **Финальный чек-лист**: `FINAL_CHECKLIST.md`

---

## Контакты и вопросы

Если есть вопросы:
1. Посмотри в `ARCHITECTURE.md`
2. Посмотри в `TESTING.md`
3. Запусти тесты: `pytest -v`
4. Посмотри код с комментариями

---

**Готово к использованию!** ✅

Начни с: `pytest tests/unit/ -v` и посмотри как работают тесты 🚀
