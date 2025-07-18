FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

COPY . .

EXPOSE 8002

RUN pip install grpcio grpcio-tools

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8002"]
