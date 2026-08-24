"""Точка входа: запускает REST-шлюз. Ожидает, что gRPC-сервер
(task_manager.server) уже запущен по адресу TASK_MANAGER_GRPC_TARGET.
"""

import os

import uvicorn

from task_manager.rest_gateway import create_app

DEFAULT_GRPC_TARGET = "localhost:50051"
DEFAULT_PORT = 8000


def main() -> None:
    grpc_target = os.environ.get("TASK_MANAGER_GRPC_TARGET", DEFAULT_GRPC_TARGET)
    app = create_app(grpc_target)
    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT)


if __name__ == "__main__":
    main()
