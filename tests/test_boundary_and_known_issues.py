"""Граничные значения (Boundary Value Analysis) и задокументированные
известные ограничения текущей реализации — зафиксированы тестом, а не
пропущены молча.
"""

import allure
import pytest

from task_manager.generated import task_manager_pb2 as pb2


@allure.feature("TaskManager")
@allure.story("Граничные значения")
@pytest.mark.boundary
def test_create_task_accepts_unicode_and_emoji_title(stub):
    title = "Купить молоко 🥛 — задача №1 (unicode test)"

    with allure.step("Создать задачу с юникодом и эмодзи в title"):
        task = stub.CreateTask(pb2.CreateTaskRequest(title=title))

    with allure.step("Title сохранился без искажений"):
        assert task.title == title


@allure.feature("TaskManager")
@allure.story("Граничные значения")
@pytest.mark.boundary
def test_create_task_accepts_very_long_title_without_truncation(stub):
    long_title = "A" * 5000

    with allure.step("Создать задачу со сверхдлинным title (5000 символов)"):
        task = stub.CreateTask(pb2.CreateTaskRequest(title=long_title))

    with allure.step("Сервер не обрезает title молча — длина совпадает"):
        assert len(task.title) == 5000


@allure.feature("TaskManager")
@allure.story("Граничные значения")
@pytest.mark.boundary
def test_create_task_title_of_only_whitespace_is_accepted(stub):
    """Граница между 'пустым' и 'непустым': сервис отклоняет только
    буквально пустую строку (`if not request.title`), а title из одних
    пробелов формально непустой и проходит проверку. Фиксируем текущее
    поведение явно, а не оставляем как случайно не замеченное."""

    with allure.step("Создать задачу с title из одних пробелов"):
        task = stub.CreateTask(pb2.CreateTaskRequest(title="   "))

    with allure.step("Запрос не отклонён — задача создана как есть"):
        assert task.title == "   "


@allure.feature("TaskManager")
@allure.story("Известные ограничения")
@pytest.mark.boundary
def test_list_tasks_has_no_pagination_known_limitation(stub):
    """ListTasks не поддерживает page_size/page_token — при большом
    количестве задач сервер вернёт вообще всё одним ответом. В проде это
    риск (объём ответа, память), контракт API это не нарушает, поэтому
    зафиксировано тестом как известное ограничение, а не как падающий тест.
    """
    task_count = 200

    with allure.step(f"Создать {task_count} задач"):
        for i in range(task_count):
            stub.CreateTask(pb2.CreateTaskRequest(title=f"task-{i}"))

    with allure.step("Запросить список без параметров пагинации — их не существует в API"):
        response = stub.ListTasks(pb2.ListTasksRequest())

    with allure.step("Сервер вернул все задачи разом — подтверждает отсутствие пагинации"):
        assert len(response.tasks) == task_count
