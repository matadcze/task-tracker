import os
import uuid
from pathlib import Path
from typing import BinaryIO

from src.core.config import settings


class LocalFileStorage:

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or settings.upload_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: BinaryIO, filename: str) -> str:

        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        file_path = self.base_dir / unique_filename

        with open(file_path, "wb") as f:
            while chunk := file.read(1024 * 1024):
                f.write(chunk)

        return unique_filename

    async def get_file_path(self, storage_path: str) -> Path:

        return self.base_dir / storage_path

    async def delete_file(self, storage_path: str) -> None:

        file_path = self.base_dir / storage_path
        if file_path.exists():
            os.remove(file_path)

    async def file_exists(self, storage_path: str) -> bool:

        file_path = self.base_dir / storage_path
        return file_path.exists()
