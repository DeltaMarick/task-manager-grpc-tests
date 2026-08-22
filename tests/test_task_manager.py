import allure
import grpc
import pytest

from task_manager.generated import task_manager_pb2 as pb2


@allure.feature("TaskManager")
@allure.story("Create task")
def test_create_task_returns_task_with_defaults(stub):
    with allure.step("Create a task with a title"):
        task = stub.CreateTask(pb2.CreateTaskRequest(title="Buy milk"))

    with allure.step("Verify defaults"):
        assert task.id
        assert task.title == "Buy milk"
        assert task.status == pb2.TaskStatus.TODO
        assert task.created_at == task.updated_at


@allure.feature("TaskManager")
@allure.story("Create task")
def test_create_task_without_title_is_rejected(stub):
    with allure.step("Create a task with an empty title"):
        with pytest.raises(grpc.RpcError) as excinfo:
            stub.CreateTask(pb2.CreateTaskRequest(title=""))

    with allure.step("Verify INVALID_ARGUMENT status"):
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@allure.feature("TaskManager")
@allure.story("Read task")
def test_get_task_returns_created_task(stub):
    with allure.step("Create a task"):
        created = stub.CreateTask(pb2.CreateTaskRequest(title="Read a book"))

    with allure.step("Fetch it by id"):
        fetched = stub.GetTask(pb2.GetTaskRequest(id=created.id))

    assert fetched == created


@allure.feature("TaskManager")
@allure.story("Read task")
def test_get_task_missing_id_returns_not_found(stub):
    with allure.step("Fetch a non-existent task"):
        with pytest.raises(grpc.RpcError) as excinfo:
            stub.GetTask(pb2.GetTaskRequest(id="does-not-exist"))

    assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


@allure.feature("TaskManager")
@allure.story("List tasks")
def test_list_tasks_returns_all_created_tasks(stub):
    with allure.step("Create three tasks"):
        titles = {"A", "B", "C"}
        for title in titles:
            stub.CreateTask(pb2.CreateTaskRequest(title=title))

    with allure.step("List all tasks"):
        response = stub.ListTasks(pb2.ListTasksRequest())

    assert {t.title for t in response.tasks} == titles


@allure.feature("TaskManager")
@allure.story("List tasks")
def test_list_tasks_filters_by_status(stub):
    with allure.step("Create a task and move it to DONE"):
        task = stub.CreateTask(pb2.CreateTaskRequest(title="Finish report"))
        stub.UpdateTask(pb2.UpdateTaskRequest(id=task.id, status=pb2.TaskStatus.DONE))
        stub.CreateTask(pb2.CreateTaskRequest(title="Still todo"))

    with allure.step("List only DONE tasks"):
        response = stub.ListTasks(
            pb2.ListTasksRequest(status_filter=pb2.TaskStatus.DONE)
        )

    assert [t.title for t in response.tasks] == ["Finish report"]


@allure.feature("TaskManager")
@allure.story("Update task")
def test_update_task_changes_only_requested_fields(stub):
    with allure.step("Create a task"):
        task = stub.CreateTask(
            pb2.CreateTaskRequest(title="Original", description="desc")
        )

    with allure.step("Update only the status"):
        updated = stub.UpdateTask(
            pb2.UpdateTaskRequest(id=task.id, status=pb2.TaskStatus.IN_PROGRESS)
        )

    with allure.step("Title and description are unchanged, status is updated"):
        assert updated.title == "Original"
        assert updated.description == "desc"
        assert updated.status == pb2.TaskStatus.IN_PROGRESS
        assert updated.updated_at >= task.updated_at


@allure.feature("TaskManager")
@allure.story("Update task")
def test_update_missing_task_returns_not_found(stub):
    with pytest.raises(grpc.RpcError) as excinfo:
        stub.UpdateTask(pb2.UpdateTaskRequest(id="does-not-exist", title="X"))

    assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


@allure.feature("TaskManager")
@allure.story("Delete task")
def test_delete_existing_task_succeeds_and_removes_it(stub):
    with allure.step("Create then delete a task"):
        task = stub.CreateTask(pb2.CreateTaskRequest(title="Temporary"))
        response = stub.DeleteTask(pb2.DeleteTaskRequest(id=task.id))

    with allure.step("Deletion reported as successful"):
        assert response.success is True

    with allure.step("Task is no longer retrievable"):
        with pytest.raises(grpc.RpcError) as excinfo:
            stub.GetTask(pb2.GetTaskRequest(id=task.id))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


@allure.feature("TaskManager")
@allure.story("Delete task")
def test_delete_missing_task_reports_failure(stub):
    response = stub.DeleteTask(pb2.DeleteTaskRequest(id="does-not-exist"))
    assert response.success is False
