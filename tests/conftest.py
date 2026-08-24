"""Общие фикстуры pytest: поднимают настоящий gRPC-сервер TaskManager
в процессе теста на свободном порту и возвращают подключённый stub.
"""

import socket
import threading
import time
from concurrent import futures
from contextlib import closing

import grpc
import pytest
import requests
import uvicorn
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from task_manager.generated import task_manager_pb2 as pb2
from task_manager.generated import task_manager_pb2_grpc as pb2_grpc
from task_manager.rest_gateway import create_app
from task_manager.server import SERVICE_NAME
from task_manager.service import TaskManagerServicer

from .grpc_client import TaskManagerClient


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


def _wait_until_ready(base_url: str, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            requests.get(f"{base_url}/health", timeout=0.5)
            return
        except requests.exceptions.ConnectionError:
            time.sleep(0.05)
    raise RuntimeError("REST-шлюз не поднялся за отведённое время")


@pytest.fixture
def rest_base_url(grpc_server):
    """Поднимает REST-шлюз (uvicorn в отдельном потоке) поверх того же
    тестового gRPC-сервера и возвращает его базовый URL."""
    app = create_app(f"localhost:{grpc_server}")
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    _wait_until_ready(base_url)

    yield base_url

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def client(stub) -> TaskManagerClient:
    """Клиент-обёртка над stub, см. tests/grpc_client.py."""
    return TaskManagerClient(stub)


@pytest.fixture
def create_task(client):
    """Фабричная фикстура: создаёт задачу со значениями по умолчанию,
    переопределяй только нужные тесту поля."""

    def _create(title: str = "Task", description: str = "") -> pb2.Task:
        return client.create_task(title=title, description=description)

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
def tasks_by_status(client, create_task) -> dict[int, pb2.Task]:
    """По одной задаче на каждый статус TaskStatus, ключ словаря — сам статус."""
    tasks = {}
    for status in (pb2.TaskStatus.TODO, pb2.TaskStatus.IN_PROGRESS, pb2.TaskStatus.DONE):
        task = create_task(title=f"task-{status}")
        if status != pb2.TaskStatus.TODO:
            task = client.update_task(task.id, status=status)
        tasks[status] = task
    return tasks
