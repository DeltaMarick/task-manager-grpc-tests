import allure
import grpc
import pytest

from task_manager.generated import task_manager_pb2 as pb2

from .helpers import assert_task_fields

ORIGINAL_TASK = {"title": "Original", "description": "desc", "status": pb2.TaskStatus.TODO}


@allure.feature("TaskManager")
@allure.story("Создание задачи")
@pytest.mark.smoke
def test_create_task_returns_task_with_defaults(client):
    with allure.step("Создать задачу с указанием title"):
        task = client.create_task(title="Buy milk")

    with allure.step("Проверить значения по умолчанию"):
        assert task.id
        assert task.created_at == task.updated_at
        assert_task_fields(task, title="Buy milk", status=pb2.TaskStatus.TODO)


@allure.feature("TaskManager")
@allure.story("Создание задачи")
@pytest.mark.negative
def test_create_task_without_title_is_rejected(client):
    with allure.step("Создать задачу с пустым title"):
        with pytest.raises(grpc.RpcError) as excinfo:
            client.create_task(title="")

    with allure.step("Проверить статус INVALID_ARGUMENT"):
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@allure.feature("TaskManager")
@allure.story("Чтение задачи")
@pytest.mark.smoke
def test_get_task_returns_created_task(client, created_task):
    with allure.step("Получить задачу по id"):
        fetched = client.get_task(created_task.id)

    with allure.step("Полученная задача совпадает с созданной"):
        assert fetched == created_task


@allure.feature("TaskManager")
@allure.story("Список задач")
@pytest.mark.smoke
def test_list_tasks_returns_all_created_tasks(client, three_task_titles):
    with allure.step("Получить список всех задач"):
        tasks = client.list_tasks()

    with allure.step("В списке присутствуют все созданные задачи"):
        assert {t.title for t in tasks} == three_task_titles


@allure.feature("TaskManager")
@allure.story("Список задач")
@pytest.mark.parametrize(
    "status",
    [pb2.TaskStatus.TODO, pb2.TaskStatus.IN_PROGRESS, pb2.TaskStatus.DONE],
    ids=["TODO", "IN_PROGRESS", "DONE"],
)
def test_list_tasks_filters_by_status(client, tasks_by_status, status):
    with allure.step("Отфильтровать задачи по статусу"):
        tasks = client.list_tasks(status=status)

    with allure.step("В списке только задача с нужным статусом"):
        assert [t.id for t in tasks] == [tasks_by_status[status].id]


@allure.feature("TaskManager")
@allure.story("Обновление задачи")
@pytest.mark.smoke
@pytest.mark.parametrize(
    "field, value",
    [
        ("title", "New title"),
        ("description", "New description"),
        ("status", pb2.TaskStatus.IN_PROGRESS),
    ],
    ids=["title-only", "description-only", "status-only"],
)
def test_update_task_changes_only_requested_field(client, create_task, field, value):
    with allure.step("Создать задачу"):
        task = create_task(title=ORIGINAL_TASK["title"], description=ORIGINAL_TASK["description"])

    with allure.step(f"Обновить только поле '{field}'"):
        updated = client.update_task(task.id, **{field: value})

    with allure.step("Изменилось только указанное поле, остальные остались прежними"):
        assert_task_fields(updated, **{**ORIGINAL_TASK, field: value})
        assert updated.updated_at >= task.updated_at


@allure.feature("TaskManager")
@allure.story("Обработка ошибок")
@pytest.mark.negative
@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda client: client.get_task("does-not-exist"), id="get"),
        pytest.param(lambda client: client.update_task("does-not-exist", title="X"), id="update"),
    ],
)
def test_missing_task_returns_not_found(client, call):
    with allure.step("Вызвать RPC с несуществующим id"):
        with pytest.raises(grpc.RpcError) as excinfo:
            call(client)

    with allure.step("Проверить статус NOT_FOUND"):
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


@allure.feature("TaskManager")
@allure.story("Удаление задачи")
@pytest.mark.smoke
def test_delete_existing_task_succeeds_and_removes_it(client, created_task):
    with allure.step("Удалить задачу"):
        success = client.delete_task(created_task.id)

    with allure.step("Удаление прошло успешно"):
        assert success is True

    with allure.step("Задача больше недоступна"):
        with pytest.raises(grpc.RpcError) as excinfo:
            client.get_task(created_task.id)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


@allure.feature("TaskManager")
@allure.story("Удаление задачи")
@pytest.mark.negative
def test_delete_missing_task_reports_failure(client):
    with allure.step("Удалить несуществующую задачу"):
        success = client.delete_task("does-not-exist")

    with allure.step("Операция сообщает о неудаче"):
        assert success is False
