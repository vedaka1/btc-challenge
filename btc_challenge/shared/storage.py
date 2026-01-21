from abc import ABC, abstractmethod

PART_SIZE = 10 * 1024 * 1024


class IS3Storage(ABC):
    @abstractmethod
    async def put_bytes(self, filename: str, data: bytes, is_temporary: bool = False) -> str:
        """
        Загружает байты обьекта в s3 хранилище
        Args:
            filename: название объекта
            data: поток байтов объекта с методами read() и seek()
            is_temporary: является ли файл временным, будет удален через 1 день (сохраняется в папку `tmp`)
        Returns:
            адрес файла в хранилище
        """
        ...

    @abstractmethod
    async def get_bytes(self, filename: str) -> bytes | None:
        """Получает байты обьекта из s3 хранилища"""
        ...
