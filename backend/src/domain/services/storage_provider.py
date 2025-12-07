from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class StorageProvider(ABC):

    @abstractmethod
    async def save_file(self, file: BinaryIO, filename: str) -> str:

        pass

    @abstractmethod
    async def get_file_path(self, storage_path: str) -> Path:

        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> None:

        pass

    @abstractmethod
    async def file_exists(self, storage_path: str) -> bool:

        pass

    @abstractmethod
    async def get_file_size(self, file: BinaryIO) -> int:

        pass
