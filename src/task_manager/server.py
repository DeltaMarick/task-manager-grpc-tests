"""Точка входа: запускает gRPC-сервер TaskManager."""

from concurrent import futures

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from task_manager.generated import task_manager_pb2_grpc as pb2_grpc
from task_manager.service import TaskManagerServicer

DEFAULT_PORT = 50051
SERVICE_NAME = "task_manager.TaskManager"


def serve(port: int = DEFAULT_PORT) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_TaskManagerServicer_to_server(TaskManagerServicer(), server)

    health_servicer = health.HealthServicer()
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set(SERVICE_NAME, health_pb2.HealthCheckResponse.SERVING)
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"TaskManager gRPC server listening on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
