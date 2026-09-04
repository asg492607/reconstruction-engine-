import hashlib
import os
import io
from pathlib import Path
from typing import Tuple, BinaryIO
from app.config import settings

class StorageManager:
    def __init__(self):
        self.backend = settings.STORAGE_BACKEND
        self.local_dir = Path(settings.LOCAL_STORAGE_DIR)
        if self.backend == "LOCAL":
            self.local_dir.mkdir(parents=True, exist_ok=True)
        elif self.backend == "MINIO":
            from minio import Minio
            self.minio_client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            # Ensure bucket exists
            try:
                if not self.minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
                    self.minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
            except Exception as e:
                # Fallback to local if MinIO is unreachable
                print(f"[StorageManager] MinIO warning: {e}. Falling back to LOCAL storage.")
                self.backend = "LOCAL"
                self.local_dir.mkdir(parents=True, exist_ok=True)

    def calculate_sha256(self, data: bytes) -> str:
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()

    async def save_file(self, case_id: str, filename: str, data: bytes) -> Tuple[str, str, int]:
        """
        Saves file immutably and returns (storage_key, sha256_hash, file_size_bytes)
        """
        sha256_hash = self.calculate_sha256(data)
        file_size = len(data)
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (".", "_", "-"))
        storage_key = f"{case_id}/{sha256_hash[:16]}_{safe_filename}"

        if self.backend == "LOCAL":
            dest_path = self.local_dir / storage_key
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(data)
        else:
            data_stream = io.BytesIO(data)
            self.minio_client.put_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=storage_key,
                data=data_stream,
                length=file_size,
            )

        return storage_key, sha256_hash, file_size

    def get_file_bytes(self, storage_key: str) -> bytes:
        if self.backend == "LOCAL":
            file_path = self.local_dir / storage_key
            if not file_path.exists():
                raise FileNotFoundError(f"File not found at storage key: {storage_key}")
            with open(file_path, "rb") as f:
                return f.read()
        else:
            response = self.minio_client.get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=storage_key
            )
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

storage_manager = StorageManager()
