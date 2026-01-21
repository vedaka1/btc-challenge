from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO

from minio import Minio, S3Error
from minio.commonconfig import ENABLED, Filter
from minio.lifecycleconfig import Expiration, LifecycleConfig, Rule
from urllib3 import BaseHTTPResponse

from btc_challenge.config import AppConfig
from btc_challenge.shared.enums import MinioPrefixes
from btc_challenge.shared.storage import PART_SIZE, IS3Storage


@lru_cache(1)
def init_minio(config: type[AppConfig] = AppConfig) -> Minio:
    minio_client = Minio(
        endpoint=config.minio.host,
        access_key=config.minio.access_key,
        secret_key=config.minio.secret_key,
        secure=bool(config.minio.secure),
    )

    bucket_exists = minio_client.bucket_exists(config.minio.bucket_name)
    if not bucket_exists:
        minio_client.make_bucket(config.minio.bucket_name)

    bucket_config = LifecycleConfig(
        [
            Rule(
                ENABLED,
                rule_filter=Filter(prefix=MinioPrefixes.TMP.value),
                rule_id="rule2",
                expiration=Expiration(days=1),
            ),
        ],
    )
    minio_client.set_bucket_lifecycle(config.minio.bucket_name, bucket_config)
    return minio_client


@dataclass(kw_only=True, slots=True, eq=False)
class MinioStorage(IS3Storage):
    s3_client: Minio
    bucket_name: str = AppConfig.minio.bucket_name
    part_size: int = PART_SIZE

    async def put_bytes(self, filename: str, data: bytes, is_temporary: bool = False) -> str:
        obj_stream = BytesIO(data)
        filename = f"{MinioPrefixes.TMP.value if is_temporary else ''}{filename}"
        self.s3_client.put_object(
            bucket_name=self.bucket_name,
            object_name=filename,
            data=obj_stream,
            length=-1,
            part_size=self.part_size,
        )
        return filename

    async def get_bytes(self, filename: str) -> bytes | None:
        response: BaseHTTPResponse | None = None
        try:
            response = self.s3_client.get_object(bucket_name=self.bucket_name, object_name=filename)
            return response.read()
        except S3Error:
            return None
        finally:
            if response:
                response.close()
                response.release_conn()


@lru_cache(1)
def init_minio_storage() -> MinioStorage:
    return MinioStorage(s3_client=init_minio())
