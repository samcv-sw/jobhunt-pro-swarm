import logging
import os
from typing import Optional, Union, BinaryIO

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    Config = None
    ClientError = Exception
    BOTO3_AVAILABLE = False

logger = logging.getLogger(__name__)

# Cloudflare R2 configuration defaults
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "jobhunt-pro-cvs")


def get_s3_client(
    account_id: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
):
    """Initializes the boto3 client for Cloudflare R2 (S3-compatible API)."""
    acc_id = account_id or os.getenv("R2_ACCOUNT_ID", "")
    acc_key = access_key or os.getenv("R2_ACCESS_KEY_ID", "")
    sec_key = secret_key or os.getenv("R2_SECRET_ACCESS_KEY", "")

    if not all([acc_id, acc_key, sec_key]):
        logger.debug(
            "Cloudflare R2 credentials not fully configured. Storage features may be degraded."
        )
        return None

    if not BOTO3_AVAILABLE or boto3 is None:
        logger.debug("boto3 is not available in current runtime environment.")
        return None

    try:
        return boto3.client(
            "s3",
            endpoint_url=f"https://{acc_id}.r2.cloudflarestorage.com",
            aws_access_key_id=acc_key,
            aws_secret_access_key=sec_key,
            config=Config(signature_version="s3v4") if Config else None,
            region_name="auto",
        )
    except Exception as e:
        logger.error(f"Failed to initialize R2 S3 client: {e}")
        return None


class StorageManager:
    """
    Manages heavy file storage (e.g., CV PDFs) using Cloudflare R2 for zero-egress, enterprise-grade edge storage.
    """

    def __init__(self):
        self._client = None

    @property
    def s3_client(self):
        if self._client is None:
            self._client = get_s3_client()
        return self._client

    @s3_client.setter
    def s3_client(self, client):
        self._client = client

    @property
    def is_configured(self) -> bool:
        """Returns True if R2 credentials are present and client is ready."""
        if hasattr(self, "_is_configured_override") and self._is_configured_override is not None:
            return self._is_configured_override
        if self._client is not None:
            return True
        acc_id = os.getenv("R2_ACCOUNT_ID", "")
        acc_key = os.getenv("R2_ACCESS_KEY_ID", "")
        sec_key = os.getenv("R2_SECRET_ACCESS_KEY", "")
        if all([acc_id, acc_key, sec_key]):
            self._client = get_s3_client(acc_id, acc_key, sec_key)
            return self._client is not None
        return False

    @is_configured.setter
    def is_configured(self, value: bool) -> None:
        self._is_configured_override = value

    @is_configured.deleter
    def is_configured(self) -> None:
        self._is_configured_override = None

    def upload_file(
        self,
        file_content: Union[bytes, bytearray, BinaryIO],
        object_name: str,
        content_type: str = "application/pdf",
    ) -> str:
        """
        Uploads a file to Cloudflare R2 and returns the public/internal URL.
        """
        client = self.s3_client
        if not client or not self.is_configured:
            logger.error("Cannot upload file: R2 client not initialized.")
            return ""

        bucket_name = os.getenv("R2_BUCKET_NAME", R2_BUCKET_NAME)
        account_id = os.getenv("R2_ACCOUNT_ID", R2_ACCOUNT_ID)

        body_bytes = (
            file_content.read() if hasattr(file_content, "read") else bytes(file_content)
        )

        try:
            client.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=body_bytes,
                ContentType=content_type,
            )
            return f"https://{bucket_name}.{account_id}.r2.cloudflarestorage.com/{object_name}"
        except ClientError as e:
            logger.error(f"Failed to upload file to R2: {e}")
            return ""
        except Exception as exc:
            logger.error(f"Unexpected error during R2 upload: {exc}")
            return ""

    def download_file(self, object_name: str) -> bytes:
        """
        Downloads a file from Cloudflare R2.
        """
        client = self.s3_client
        if not client or not self.is_configured:
            logger.error("Cannot download file: R2 client not initialized.")
            return b""

        bucket_name = os.getenv("R2_BUCKET_NAME", R2_BUCKET_NAME)
        try:
            response = client.get_object(Bucket=bucket_name, Key=object_name)
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to download file from R2: {e}")
            return b""
        except Exception as exc:
            logger.error(f"Unexpected error during R2 download: {exc}")
            return b""

    def delete_file(self, object_name: str) -> bool:
        """
        Deletes a file from Cloudflare R2.
        """
        client = self.s3_client
        if not client or not self.is_configured:
            logger.error("Cannot delete file: R2 client not initialized.")
            return False

        bucket_name = os.getenv("R2_BUCKET_NAME", R2_BUCKET_NAME)
        try:
            client.delete_object(Bucket=bucket_name, Key=object_name)
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from R2: {e}")
            return False
        except Exception as exc:
            logger.error(f"Unexpected error during R2 delete: {exc}")
            return False


storage_manager = StorageManager()

