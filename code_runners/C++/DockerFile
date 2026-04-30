FROM gcc:13

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir --break-system-packages fastapi uvicorn

RUN mkdir -p /usr/local/include/nlohmann
COPY json.hpp /usr/local/include/nlohmann/json.hpp
COPY run.sh .
COPY server.py .
RUN chmod +x run.sh

EXPOSE 9000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9000"]
