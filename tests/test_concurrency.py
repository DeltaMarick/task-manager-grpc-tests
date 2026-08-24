"""Тесты на параллельный доступ: проверяют, что self._lock в service.py
защищает данные от гонок при одновременных запросах.
"""

from concurrent.futures import ThreadPoolExecutor

import allure
import pytest

from task_manager.generated import task_manager_pb2 as pb2


@allure.feature("TaskManager")
@allure.story("Конкурентный доступ")
@pytest.mark.concurrency
def test_concurrent_creates_do_not_lose_or_duplicate_tasks(stub):
    task_count = 50

    with allure.step(f"Создать {task_count} задач параллельно из разных потоков"):
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [
                pool.submit(stub.CreateTask, pb2.CreateTaskRequest(title=f"task-{i}"))
                for i in range(task_count)
            ]
            created = [f.result() for f in futures]

    with allure.step("Все id уникальны — ни одна задача не потерялась и не задвоилась"):
        ids = {task.id for task in created}
        assert len(ids) == task_count

    with allure.step("Сервер хранит ровно столько же задач"):
        response = stub.ListTasks(pb2.ListTasksRequest())
        assert len(response.tasks) == task_count


@allure.feature("TaskManager")
@allure.story("Конкурентный доступ")
@pytest.mark.concurrency
def test_concurrent_updates_to_same_task_do_not_corrupt_state(stub, created_task):
    update_count = 20

    with allure.step(f"Отправить {update_count} параллельных обновлений title у одной задачи"):
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [
                pool.submit(
                    stub.UpdateTask,
                    pb2.UpdateTaskRequest(id=created_task.id, title=f"title-{i}"),
                )
                for i in range(update_count)
            ]
            responses = [f.result() for f in futures]

    with allure.step("Ни один из вызовов не упал с ошибкой"):
        assert len(responses) == update_count

    with allure.step("Финальное состояние — один из отправленных вариантов, а не смесь полей"):
        final = stub.GetTask(pb2.GetTaskRequest(id=created_task.id))
        sent_titles = {f"title-{i}" for i in range(update_count)}
        assert final.title in sent_titles
