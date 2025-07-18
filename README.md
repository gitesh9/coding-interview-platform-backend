# coding-interview-platform-backend

<!-- docker command to run the app -->
docker compose up --build


docker-compose down -v
docker-compose build --no-cache
docker-compose up

#for grpc output files
python -m grpc_tools.protoc -I=./proto --python_out=. --grpc_python_out=. proto/problem.proto