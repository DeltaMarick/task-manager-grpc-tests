# task-manager-grpc-tests

[![CI](https://github.com/DeltaMarick/task-manager-grpc-tests/actions/workflows/ci.yml/badge.svg)](https://github.com/DeltaMarick/task-manager-grpc-tests/actions/workflows/ci.yml)

gRPC-сервис `TaskManager` (CRUD над задачами, in-memory хранилище)
на Python, автотесты на pytest поверх реального gRPC-сервера, отчёты Allure.
Поверх gRPC есть REST-шлюз (FastAPI), транслирующий HTTP/JSON в те же
gRPC-вызовы — бизнес-логика не дублируется, тестируется один и тот же
контракт по двум протоколам.

## Структура

```
proto/                          .proto-контракт сервиса
scripts/generate_proto.py       генерация Python-стабов из .proto
src/task_manager/
  service.py                    бизнес-логика (TaskManagerServicer)
  server.py                     точка входа: поднимает gRPC-сервер
  rest_gateway.py                REST-приложение (FastAPI), зовёт gRPC-стаб
  rest_server.py                 точка входа: поднимает REST-шлюз
  generated/                    сгенерированные *_pb2*.py (в .gitignore)
tests/
  conftest.py                   фикстуры: поднимают сервер на свободном порту
  test_task_manager.py          CRUD-сценарии по gRPC
  test_rest_gateway.py          те же сценарии по REST (requests)
  test_health.py                grpc.health.v1
  test_deadlines.py             таймауты и отмена вызова
  test_concurrency.py           параллельный доступ (race condition)
  test_boundary_and_known_issues.py  граничные значения, известные ограничения
```

## Установка

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Генерация gRPC-стабов

Стабы не хранятся в репозитории — генерируются из `proto/task_manager.proto`:

```powershell
python scripts/generate_proto.py
```

Запускать заново при каждом изменении `.proto`.

## Запуск сервера

```powershell
python -m task_manager.server
```

(добавьте `src` в `PYTHONPATH`, либо запускайте из `src/`)

## Запуск REST-шлюза

Требует уже запущенный gRPC-сервер (см. выше):

```powershell
python -m task_manager.rest_server
```

Swagger UI (генерируется FastAPI автоматически) — http://localhost:8000/docs.
Адрес gRPC-сервера можно переопределить переменной окружения
`TASK_MANAGER_GRPC_TARGET` (по умолчанию `localhost:50051`).

## Запуск тестов

```powershell
pytest
```

Тесты сами поднимают сервер в отдельном потоке на свободном порту — внешний
сервер запускать не нужно. Результаты Allure пишутся в `allure-results/`
(настроено в `pytest.ini`).

Каждый прогон также считает покрытие кода (`pytest-cov`): краткий отчёт —
в консоли, подробный — в `htmlcov/index.html`. `src/task_manager/server.py`
намеренно не покрыт юнит-тестами — это просто точка входа, поднимающая
настоящий сервер и блокирующая выполнение (`wait_for_termination`); та же
логика запуска сервера уже проверяется фикстурой `grpc_server` в
`conftest.py`, только на случайном порту.

## Линтер и форматтер

```powershell
ruff check .
black --check .
```

## Просмотр Allure-отчёта

Нужен установленный Allure commandline (`scoop install allure` /
[скачать релиз](https://github.com/allure-framework/allure2/releases)).

```powershell
allure serve allure-results
# либо статический отчёт:
allure generate allure-results -o allure-report --clean
```
