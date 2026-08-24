"""Тесты стандартного health-check сервиса grpc.health.v1 — по нему
Kubernetes (readiness/liveness) и балансировщики нагрузки проверяют,
жив ли сервис, не зная ничего о его бизнес-API.
"""

import allure
import grpc
import pytest
from grpc_health.v1 import health_pb2

from task_manager.server import SERVICE_NAME


@allure.feature("Health check")
@allure.story("Общий статус сервера")
def test_overall_server_health_is_serving(health_stub):
    with allure.step("Запросить общий статус сервера (пустое имя сервиса)"):
        response = health_stub.Check(health_pb2.HealthCheckRequest(service=""))

    with allure.step("Статус SERVING"):
        assert response.status == health_pb2.HealthCheckResponse.SERVING


@allure.feature("Health check")
@allure.story("Статус конкретного сервиса")
def test_task_manager_service_health_is_serving(health_stub):
    with allure.step("Запросить статус конкретно сервиса task_manager.TaskManager"):
        response = health_stub.Check(health_pb2.HealthCheckRequest(service=SERVICE_NAME))

    with allure.step("Статус SERVING"):
        assert response.status == health_pb2.HealthCheckResponse.SERVING


@allure.feature("Health check")
@allure.story("Неизвестный сервис")
@pytest.mark.negative
def test_unknown_service_health_check_fails(health_stub):
    with allure.step("Запросить статус несуществующего сервиса"):
        with pytest.raises(grpc.RpcError) as excinfo:
            health_stub.Check(health_pb2.HealthCheckRequest(service="does.not.Exist"))

    with allure.step("Сервер отвечает NOT_FOUND"):
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND
