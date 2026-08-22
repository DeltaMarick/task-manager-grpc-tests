"""Shared pytest fixtures: spins up a real TaskManager gRPC server
in-process on a free port for each test, and hands back a connected stub.
"""
from concurrent import futures
from contextlib import closing
import socket

import grpc
import pytest

from task_manager.generated import task_manager_pb2_grpc as pb2_grpc
from task_manager.service import TaskManagerServicer


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("localhost", 0))
        return sock.getsockname()[1]


@pytest.fixture
def grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    pb2_grpc.add_TaskManagerServicer_to_server(TaskManagerServicer(), server)
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
