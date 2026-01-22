# Запуск проекта
## Docker-compose
```bash
cp .env.example .env
```
Set up .env variables:
```
BOT_TOKEN=
DATABASE_PATH=./app.db

MINIO_HOST=localhost:9000 # or minio:9000 for docker compose
MINIO_BUCKET_NAME=btc
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_SECURE=false
MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
```

You can also pass container name with `cont=<container_name>` argument where its possible

- #### Run project (supports `cont=`)
    ```bash
    make dev
    ```
- #### Shutdown project
    ```bash
    make down
    ```
- #### View last 500 logs (supports `cont=`)
    ```bash
    make logs
    ```
- #### Restart (supports `cont=`)
    ```bash
    make restart
    ```

