FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/ proto/
COPY scripts/ scripts/
COPY src/ src/
RUN python scripts/generate_proto.py

ENV PYTHONPATH=/app/src

EXPOSE 50051

CMD ["python", "-m", "task_manager.server"]
