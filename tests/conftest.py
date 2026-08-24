"""Общие фикстуры pytest: поднимают настоящий gRPC-сервер TaskManager
в процессе теста на свободном порту и возвращают подключённый stub.
"""

import socket
from concurrent import futures
from contextlib import closing

import grpc
import pytest
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from task_manager.generated import task_manager_pb2 as pb2
from task_manager.generated import task_manager_pb2_grpc as pb2_grpc
from task_manager.server import SERVICE_NAME
from task_manager.service import TaskManagerServicer


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("localhost", 0))
        return sock.getsockname()[1]


@pytest.fixture
def grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    pb2_grpc.add_TaskManagerServicer_to_server(TaskManagerServicer(), server)

    health_servicer = health.HealthServicer()
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set(SERVICE_NAME, health_pb2.HealthCheckResponse.SERVING)
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    port = _free_port()
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    yield port
    server.stop(grace=None)


@pytest.fixture
def stub(grpc_server):
    channel = grpc.insecure_channel(f"localhost:{grpc_server}")
    grpc.channel_ready_future(channel).result(timeout=5)
    yield pb2_grpc.TaskManagerStub(channel)
    channel.close()


@pytest.fixture
def health_stub(grpc_server):
    channel = grpc.insecure_channel(f"localhost:{grpc_server}")
    grpc.channel_ready_future(channel).result(timeout=5)
    yield health_pb2_grpc.HealthStub(channel)
    channel.close()


@pytest.fixture
def create_task(stub):
    """Фабричная фикстура: создаёт задачу со значениями по умолчанию,
    переопределяй только нужные тесту поля."""

    def _create(title: str = "Task", description: str = "") -> pb2.Task:
        return stub.CreateTask(pb2.CreateTaskRequest(title=title, description=description))

    return _create


@pytest.fixture
def created_task(create_task) -> pb2.Task:
    """Одна созданная задача со значениями по умолчанию —
    для тестов, которым не важно её содержимое."""
    return create_task()


@pytest.fixture
def three_task_titles(create_task) -> set[str]:
    """Создаёт три задачи и возвращает их заголовки."""
    titles = {"A", "B", "C"}
    for title in titles:
        create_task(title=title)
    return titles


@pytest.fixture
def tasks_by_status(stub, create_task) -> dict[int, pb2.Task]:
    """По одной задаче на каждый статус TaskStatus, ключ словаря — сам статус."""
    tasks = {}
    for status in (pb2.TaskStatus.TODO, pb2.TaskStatus.IN_PROGRESS, pb2.TaskStatus.DONE):
        task = create_task(title=f"task-{status}")
        if status != pb2.TaskStatus.TODO:
            task = stub.UpdateTask(pb2.UpdateTaskRequest(id=task.id, status=status))
        tasks[status] = task
    return tasks
