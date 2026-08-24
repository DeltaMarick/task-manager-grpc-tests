"""Клиент-обёртка над сырым gRPC-стабом TaskManager.

Прячет protobuf-детали (конструирование Request-объектов, HasField-семантику
частичного обновления в UpdateTask) за понятными методами — в UI-автоматизации
то же самое называют Page Object, здесь это Service Object / API Client для
gRPC. Тесты работают с бизнес-действиями ("создать задачу"), а не с деталями
протокола.
"""

from task_manager.generated import task_manager_pb2 as pb2
from task_manager.generated import task_manager_pb2_grpc as pb2_grpc


class TaskManagerClient:
    def __init__(self, stub: pb2_grpc.TaskManagerStub) -> None:
        self._stub = stub

    def create_task(self, title: str, description: str = "") -> pb2.Task:
        return self._stub.CreateTask(pb2.CreateTaskRequest(title=title, description=description))

    def get_task(self, task_id: str) -> pb2.Task:
        return self._stub.GetTask(pb2.GetTaskRequest(id=task_id))

    def list_tasks(self, status: int | None = None) -> list[pb2.Task]:
        request = pb2.ListTasksRequest()
        if status is not None:
            request.status_filter = status
        return list(self._stub.ListTasks(request).tasks)

    def update_task(
        self,
        task_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        status: int | None = None,
    ) -> pb2.Task:
        request = pb2.UpdateTaskRequest(id=task_id)
        if title is not None:
            request.title = title
        if description is not None:
            request.description = description
        if status is not None:
            request.status = status
        return self._stub.UpdateTask(request)

    def delete_task(self, task_id: str) -> bool:
        return self._stub.DeleteTask(pb2.DeleteTaskRequest(id=task_id)).success
