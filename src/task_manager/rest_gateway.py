"""REST-шлюз поверх gRPC-сервиса TaskManager: транслирует HTTP/JSON-запросы
в gRPC-вызовы к уже запущенному TaskManagerServicer. Бизнес-логика не
дублируется — шлюз только переупаковывает запрос/ответ в другой протокол.
"""

import grpc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from task_manager.generated import task_manager_pb2 as pb2
from task_manager.generated import task_manager_pb2_grpc as pb2_grpc

GRPC_STATUS_TO_HTTP = {
    grpc.StatusCode.NOT_FOUND: 404,
    grpc.StatusCode.INVALID_ARGUMENT: 400,
}

STATUS_NAME_TO_ENUM = {
    "TODO": pb2.TaskStatus.TODO,
    "IN_PROGRESS": pb2.TaskStatus.IN_PROGRESS,
    "DONE": pb2.TaskStatus.DONE,
}
STATUS_ENUM_TO_NAME = {value: name for name, value in STATUS_NAME_TO_ENUM.items()}


class CreateTaskBody(BaseModel):
    title: str
    description: str = ""


class UpdateTaskBody(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


def _task_to_dict(task: pb2.Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": STATUS_ENUM_TO_NAME[task.status],
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def _status_enum(status_name: str) -> int:
    if status_name not in STATUS_NAME_TO_ENUM:
        raise HTTPException(status_code=400, detail=f"unknown status: {status_name}")
    return STATUS_NAME_TO_ENUM[status_name]


def create_app(grpc_target: str) -> FastAPI:
    """Создаёт REST-приложение, обращающееся к gRPC-серверу по адресу grpc_target."""
    app = FastAPI(title="TaskManager REST Gateway")
    channel = grpc.insecure_channel(grpc_target)
    stub = pb2_grpc.TaskManagerStub(channel)

    def _call(rpc, request):
        try:
            return rpc(request)
        except grpc.RpcError as exc:
            status_code = GRPC_STATUS_TO_HTTP.get(exc.code(), 500)
            raise HTTPException(status_code=status_code, detail=exc.details()) from exc

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/tasks", status_code=201)
    def create_task(body: CreateTaskBody) -> dict:
        request = pb2.CreateTaskRequest(title=body.title, description=body.description)
        return _task_to_dict(_call(stub.CreateTask, request))

    @app.get("/tasks/{task_id}")
    def get_task(task_id: str) -> dict:
        return _task_to_dict(_call(stub.GetTask, pb2.GetTaskRequest(id=task_id)))

    @app.get("/tasks")
    def list_tasks(status: str | None = None) -> list[dict]:
        request = pb2.ListTasksRequest()
        if status is not None:
            request.status_filter = _status_enum(status)
        response = _call(stub.ListTasks, request)
        return [_task_to_dict(task) for task in response.tasks]

    @app.patch("/tasks/{task_id}")
    def update_task(task_id: str, body: UpdateTaskBody) -> dict:
        request = pb2.UpdateTaskRequest(id=task_id)
        if body.title is not None:
            request.title = body.title
        if body.description is not None:
            request.description = body.description
        if body.status is not None:
            request.status = _status_enum(body.status)
        return _task_to_dict(_call(stub.UpdateTask, request))

    @app.delete("/tasks/{task_id}")
    def delete_task(task_id: str) -> dict:
        response = _call(stub.DeleteTask, pb2.DeleteTaskRequest(id=task_id))
        return {"success": response.success}

    return app
