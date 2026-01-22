import json

from btc_challenge.environment import get_env_var


class TelegramConfig:
    bot_token: str = get_env_var(key="BOT_TOKEN", cast_to=str)
    admin_ids: list[int] = get_env_var(key="ADMIN_IDS", cast_to=json.loads, default=[])


class SqliteConfig:
    database_path: str = get_env_var("DATABASE_PATH", str, default="./app.db")

    @property
    def async_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.database_path}"

    @property
    def sync_url(self) -> str:
        return f"sqlite:///{self.database_path}"


class MinioConfig:
    bucket_name: str = get_env_var("MINIO_BUCKET_NAME", str)
    host: str = get_env_var("MINIO_HOST", str)
    access_key: str = get_env_var("MINIO_ACCESS_KEY", str)
    secret_key: str = get_env_var("MINIO_SECRET_KEY", str)
    secure: bool = get_env_var("MINIO_SECURE", bool, default=False)


class AppConfig:
    telegram: TelegramConfig = TelegramConfig()
    sqlite: SqliteConfig = SqliteConfig()
    minio: MinioConfig = MinioConfig()
