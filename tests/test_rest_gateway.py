"""Тесты REST-шлюза: та же бизнес-логика TaskManager, что и в gRPC-тестах,
но проверяется по HTTP через requests — показывает, что фреймворк умеет
работать с обоими протоколами на одном и том же контракте.
"""

import allure
import pytest
import requests


@allure.feature("REST Gateway")
@allure.story("Создание задачи")
@pytest.mark.smoke
def test_create_task_returns_201_with_task_body(rest_base_url):
    with allure.step("POST /tasks с title"):
        response = requests.post(f"{rest_base_url}/tasks", json={"title": "Buy milk"})

    with allure.step("201 Created, тело содержит id и статус TODO"):
        assert response.status_code == 201
        body = response.json()
        assert body["id"]
        assert body["title"] == "Buy milk"
        assert body["status"] == "TODO"


@allure.feature("REST Gateway")
@allure.story("Создание задачи")
@pytest.mark.negative
def test_create_task_without_title_returns_400(rest_base_url):
    with allure.step("POST /tasks с пустым title"):
        response = requests.post(f"{rest_base_url}/tasks", json={"title": ""})

    with allure.step("400 Bad Request"):
        assert response.status_code == 400


@allure.feature("REST Gateway")
@allure.story("Чтение задачи")
@pytest.mark.smoke
def test_get_task_returns_created_task(rest_base_url):
    created = requests.post(f"{rest_base_url}/tasks", json={"title": "Task"}).json()

    with allure.step("GET /tasks/{id}"):
        response = requests.get(f"{rest_base_url}/tasks/{created['id']}")

    with allure.step("200 OK, тело совпадает с созданной задачей"):
        assert response.status_code == 200
        assert response.json() == created


@allure.feature("REST Gateway")
@allure.story("Чтение задачи")
@pytest.mark.negative
def test_get_missing_task_returns_404(rest_base_url):
    with allure.step("GET /tasks/{id} для несуществующего id"):
        response = requests.get(f"{rest_base_url}/tasks/does-not-exist")

    with allure.step("404 Not Found"):
        assert response.status_code == 404


@allure.feature("REST Gateway")
@allure.story("Список задач")
@pytest.mark.smoke
def test_list_tasks_filters_by_status(rest_base_url):
    requests.post(f"{rest_base_url}/tasks", json={"title": "todo-task"})
    in_progress = requests.post(f"{rest_base_url}/tasks", json={"title": "in-progress-task"}).json()
    requests.patch(f"{rest_base_url}/tasks/{in_progress['id']}", json={"status": "IN_PROGRESS"})

    with allure.step("GET /tasks?status=IN_PROGRESS"):
        response = requests.get(f"{rest_base_url}/tasks", params={"status": "IN_PROGRESS"})

    with allure.step("В списке только задача с этим статусом"):
        assert response.status_code == 200
        tasks = response.json()
        assert [t["id"] for t in tasks] == [in_progress["id"]]


@allure.feature("REST Gateway")
@allure.story("Обновление задачи")
@pytest.mark.smoke
def test_update_task_changes_only_requested_field(rest_base_url):
    created = requests.post(
        f"{rest_base_url}/tasks", json={"title": "Original", "description": "desc"}
    ).json()

    with allure.step("PATCH /tasks/{id} с новым title"):
        response = requests.patch(
            f"{rest_base_url}/tasks/{created['id']}", json={"title": "New title"}
        )

    with allure.step("title изменился, остальные поля — нет"):
        updated = response.json()
        assert updated["title"] == "New title"
        assert updated["description"] == "desc"
        assert updated["status"] == "TODO"


@allure.feature("REST Gateway")
@allure.story("Удаление задачи")
@pytest.mark.smoke
def test_delete_existing_task_returns_success_and_removes_it(rest_base_url):
    created = requests.post(f"{rest_base_url}/tasks", json={"title": "To delete"}).json()

    with allure.step("DELETE /tasks/{id}"):
        response = requests.delete(f"{rest_base_url}/tasks/{created['id']}")

    with allure.step("success: true"):
        assert response.status_code == 200
        assert response.json()["success"] is True

    with allure.step("Задача больше не доступна"):
        follow_up = requests.get(f"{rest_base_url}/tasks/{created['id']}")
        assert follow_up.status_code == 404
