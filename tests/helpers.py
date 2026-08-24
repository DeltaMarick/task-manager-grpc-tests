"""Небольшие помощники для сборки проверок в тестах."""


def assert_task_fields(task, **expected) -> None:
    """Сверяет только перечисленные поля задачи с ожидаемыми значениями."""
    for field, value in expected.items():
        assert getattr(task, field) == value, f"{field}: {getattr(task, field)!r} != {value!r}"
