"""In-memory TaskManager gRPC servicer implementation."""
import time
import uuid
from threading import Lock

import grpc

from task_manager.generated import task_manager_pb2 as pb2
from task_manager.generated import task_manager_pb2_grpc as pb2_grpc


class TaskManagerServicer(pb2_grpc.TaskManagerServicer):
    """Stores tasks in memory, keyed by id. Not persisted across restarts."""

    def __init__(self) -> None:
        self._tasks: dict[str, pb2.Task] = {}
        self._lock = Lock()

    def CreateTask(self, request, context):
        if not request.title:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "title is required")

        now = int(time.time())
        task = pb2.Task(
            id=str(uuid.uuid4()),
            title=request.title,
            description=request.description,
            status=pb2.TaskStatus.TODO,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def GetTask(self, request, context):
        with self._lock:
            task = self._tasks.get(request.id)
        if task is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"task {request.id} not found")
        return task

    def ListTasks(self, request, context):
        with self._lock:
            tasks = list(self._tasks.values())
        if request.HasField("status_filter"):
            tasks = [t for t in tasks if t.status == request.status_filter]
        return pb2.ListTasksResponse(tasks=tasks)

    def UpdateTask(self, request, context):
        with self._lock:
            task = self._tasks.get(request.id)
            if task is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"task {request.id} not found")

            updated = pb2.Task()
            updated.CopyFrom(task)
            if request.HasField("title"):
                updated.title = request.title
            if request.HasField("description"):
                updated.description = request.description
            if request.HasField("status"):
                updated.status = request.status
            updated.updated_at = int(time.time())

            self._tasks[request.id] = updated
        return updated

    def DeleteTask(self, request, context):
        with self._lock:
            existed = self._tasks.pop(request.id, None) is not None
        return pb2.DeleteTaskResponse(success=existed)
