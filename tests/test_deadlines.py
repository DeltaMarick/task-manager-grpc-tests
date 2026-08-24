"""Тесты на deadline (таймаут клиента) и отмену вызова — специфика gRPC:
клиент сам решает, сколько готов ждать ответ, и может передумать до его
получения. Сервис в этом файле искусственно замедлен интерцептором, иначе
реальный TaskManagerServicer отвечает быстрее, чем успевает сработать
таймаут или дойти отмена.
"""

import time
from concurrent import futures

import allure
import grpc
import pytest

from task_manager.generated import task_manager_pb2 as pb2
from task_manager.generated import task_manager_pb2_grpc as pb2_grpc
from task_manager.service import TaskManagerServicer

SERVER_DELAY_SECONDS = 0.5


class _DelayInterceptor(grpc.ServerInterceptor):
    """Задерживает каждый вызов на фиксированное время — имитирует медленный
    сервер, чтобы детерминированно ловить DEADLINE_EXCEEDED и CANCELLED."""

    def intercept_service(self, continuation, handler_call_details):
        time.sleep(SERVER_DELAY_SECONDS)
        return continuation(handler_call_details)


@pytest.fixture
def slow_stub():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        interceptors=[_DelayInterceptor()],
    )
    pb2_grpc.add_TaskManagerServicer_to_server(TaskManagerServicer(), server)
    port = server.add_insecure_port("localhost:0")
    server.start()

    channel = grpc.insecure_channel(f"localhost:{port}")
    yield pb2_grpc.TaskManagerStub(channel)
    channel.close()
    server.stop(grace=None)


@allure.feature("TaskManager")
@allure.story("Deadline и отмена")
@pytest.mark.negative
def test_call_exceeding_deadline_is_aborted(slow_stub):
    with allure.step("Вызвать метод с таймаутом короче реального времени ответа сервера"):
        with pytest.raises(grpc.RpcError) as excinfo:
            slow_stub.CreateTask(pb2.CreateTaskRequest(title="Too slow"), timeout=0.1)

    with allure.step("Клиент получает DEADLINE_EXCEEDED, а не зависает"):
        assert excinfo.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED


@allure.feature("TaskManager")
@allure.story("Deadline и отмена")
def test_cancelled_call_reports_cancelled_status(slow_stub):
    with allure.step("Запустить вызов асинхронно и отменить его до получения ответа"):
        future_call = slow_stub.CreateTask.future(pb2.CreateTaskRequest(title="Cancel me"))
        future_call.cancel()

    with allure.step("Вызов сообщает об отмене"):
        assert future_call.cancelled()
