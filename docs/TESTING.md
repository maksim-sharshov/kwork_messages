# 🧪 Руководство по запуску тестов

## Быстрый старт

### 1. Установить зависимости для тестирования
```bash
pip install pytest pytest-asyncio pytest-cov
```

### 2. Запустить все тесты
```bash
pytest
```

**Ожидаемый результат**:
```
tests/unit/test_file_service.py::test_download_file_success PASSED
tests/unit/test_file_service.py::test_download_file_http_error PASSED
tests/unit/test_file_service.py::test_parse_document_success PASSED
tests/unit/test_file_service.py::test_parse_document_unsupported_format PASSED
tests/unit/test_file_service.py::test_send_to_telegram_photo PASSED
tests/unit/test_file_service.py::test_send_to_telegram_document PASSED
tests/unit/test_file_service.py::test_send_to_telegram_error PASSED
tests/unit/test_file_service.py::test_process_files_from_message_success PASSED

tests/unit/test_message_processor.py::test_ai_processor_can_process_when_flag_false PASSED
tests/unit/test_message_processor.py::test_ai_processor_cannot_process_when_flag_true PASSED
tests/unit/test_message_processor.py::test_manager_processor_can_process PASSED
tests/unit/test_message_processor.py::test_extract_kwork_user_id_from_mfrom PASSED
tests/unit/test_message_processor.py::test_extract_kwork_user_id_from_msgfrom PASSED
tests/unit/test_message_processor.py::test_send_to_telegram_success PASSED
tests/unit/test_message_processor.py::test_send_to_telegram_error PASSED

======================== 15 passed in 0.85s ========================
```

---

## Команды для запуска

### Все тесты с подробностью
```bash
pytest -v
```

### Только unit тесты
```bash
pytest tests/unit/ -v
```

### Конкретный файл
```bash
pytest tests/unit/test_file_service.py -v
```

### Конкретный тест
```bash
pytest tests/unit/test_file_service.py::test_download_file_success -v
```

### С вывода логов
```bash
pytest -v -s
```

### Остановиться на первой ошибке
```bash
pytest -x
```

### Только ошибки
```bash
pytest --tb=short -v
```

---

## Покрытие кода (Code Coverage)

### Базовое покрытие
```bash
pytest --cov=services --cov=manager --cov-report=term-missing
```

### HTML отчёт
```bash
pytest --cov=services --cov=manager --cov-report=html
```

Откроется файл `htmlcov/index.html` с подробным отчётом.

### Минимальный порог покрытия
```bash
pytest --cov=services --cov-fail-under=80
```

---

## Фильтрация тестов

### По названию
```bash
# Все тесты с "processor" в имени
pytest -v -k "processor"

# Все тесты с "file" в имени
pytest -v -k "file"

# Исключить "error"
pytest -v -k "not error"
```

### По маркерам
```bash
pytest -m asyncio -v
pytest -m unit -v
```

---

## VS Code

### Запуск через расширение Python
1. Установить расширение "Python Test Explorer"
2. Откроется панель с тестами слева
3. Кликнуть "Run" на тесте или файле

### Команда палитры (Ctrl+Shift+P)
```
Python: Discover Tests
Python: Run Tests
Python: Run Failed Tests
```

---

## GitHub Actions / CI/CD

### Пример workflow (`.github/workflows/tests.yml`)
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: 3.10
    
    - run: pip install -r requirements.txt
    - run: pip install pytest pytest-asyncio pytest-cov
    
    - run: pytest --cov=services --cov=manager --cov-report=xml
    
    - uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

## Структура тестов

```
tests/
├── __init__.py
├── conftest.py                          # Fixtures
│   ├── mock_kwork_account
│   ├── mock_bot
│   ├── mock_gpt_handler
│   ├── sample_message
│   ├── sample_message_with_file
│   └── sample_dialog
│
└── unit/
    ├── __init__.py
    ├── test_file_service.py             # 8 тестов
    │   ├── test_download_file_success
    │   ├── test_download_file_http_error
    │   ├── test_parse_document_success
    │   ├── test_parse_document_unsupported_format
    │   ├── test_send_to_telegram_photo
    │   ├── test_send_to_telegram_document
    │   ├── test_send_to_telegram_error
    │   └── test_process_files_from_message_success
    │
    └── test_message_processor.py        # 7 тестов
        ├── test_ai_processor_can_process_when_flag_false
        ├── test_ai_processor_cannot_process_when_flag_true
        ├── test_manager_processor_can_process
        ├── test_extract_kwork_user_id_from_mfrom
        ├── test_extract_kwork_user_id_from_msgfrom
        ├── test_send_to_telegram_success
        └── test_send_to_telegram_error
```

---

## Типичные ошибки и решения

### ❌ `ModuleNotFoundError: No module named 'pytest'`
**Решение**:
```bash
pip install pytest pytest-asyncio
```

### ❌ `asyncio.InvalidStateError`
**Решение**: убедитесь что в `conftest.py` правильный `event_loop` fixture

### ❌ `mock не работает`
**Решение**: используйте `patch` перед импортом модуля, не после

### ❌ `Тесты зависают`
**Решение**: проверьте что нет бесконечных циклов, используйте timeout:
```bash
pytest --timeout=5
```

---

## Полная проверка (перед коммитом)

```bash
# Type checking
mypy services/ manager/ integrations/ --strict

# Lint
pylint services/ manager/ integrations/

# Format
black services/ manager/ integrations/ --check

# Тесты
pytest tests/ -v --cov=services --cov=manager

# Все вместе
bash -c "mypy services/ manager/ integrations/ --strict && pytest tests/ -v --cov=services --cov=manager --cov-fail-under=80"
```

---

## Отладка конкретного теста

### С breakpoint
```python
# В тесте
import pdb
pdb.set_trace()

pytest tests/unit/test_file_service.py::test_download_file_success -s
```

### С логами
```bash
pytest -s -v --log-cli-level=DEBUG
```

### С traceback
```bash
pytest -v --tb=long
```

---

## Ссылки

- [pytest документация](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Mock объекты](https://docs.python.org/3/library/unittest.mock.html)

---

## Что дальше?

✅ Unit тесты работают (15 тестов)  
⏳ TODO: Integration тесты (E2E)  
⏳ TODO: Увеличить покрытие до 90%+  
⏳ TODO: Добавить tests в CI/CD pipeline

---

**Готово к использованию!** 🎉
