# grpc-pet-project

Pet-проект: gRPC-сервис `TaskManager` (CRUD над задачами, in-memory хранилище)
на Python, автотесты на pytest поверх реального gRPC-сервера, отчёты Allure.

## Структура

```
proto/                          .proto-контракт сервиса
scripts/generate_proto.py       генерация Python-стабов из .proto
src/task_manager/
  service.py                    бизнес-логика (TaskManagerServicer)
  server.py                     точка входа: поднимает gRPC-сервер
  generated/                    сгенерированные *_pb2*.py (в .gitignore)
tests/
  conftest.py                   фикстуры: поднимают сервер на свободном порту
  test_task_manager.py          сценарии CRUD с Allure-разметкой
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

## Запуск тестов

```powershell
pytest
```

Тесты сами поднимают сервер в отдельном потоке на свободном порту — внешний
сервер запускать не нужно. Результаты Allure пишутся в `allure-results/`
(настроено в `pytest.ini`).

## Просмотр Allure-отчёта

Нужен установленный Allure commandline (`scoop install allure` /
[скачать релиз](https://github.com/allure-framework/allure2/releases)).

```powershell
allure serve allure-results
# либо статический отчёт:
allure generate allure-results -o allure-report --clean
```
