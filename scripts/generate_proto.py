"""Перегенерирует Python gRPC-стабы из proto/task_manager.proto.

Запускать из корня проекта:
    python scripts/generate_proto.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT / "proto"
OUT_DIR = ROOT / "src" / "task_manager" / "generated"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    init_file = OUT_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--pyi_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        str(PROTO_DIR / "task_manager.proto"),
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)

    # grpc_tools генерирует `import task_manager_pb2 as ...` (абсолютный импорт),
    # который ломается, когда файл лежит внутри пакета. Переписываем его
    # на относительный импорт пакета.
    grpc_file = OUT_DIR / "task_manager_pb2_grpc.py"
    text = grpc_file.read_text()
    text = text.replace(
        "import task_manager_pb2 as task__manager__pb2",
        "from . import task_manager_pb2 as task__manager__pb2",
    )
    grpc_file.write_text(text)

    print(f"Generated stubs in {OUT_DIR}")


if __name__ == "__main__":
    main()
