import os
import boto3
import logging
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger(__name__)

# Cloudflare R2 configuration
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "jobhunt-pro-cvs")


def get_s3_client():
    """Initializes the boto3 client for Cloudflare R2 (S3-compatible API)."""
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        logger.warning(
            "Cloudflare R2 credentials not fully configured. Storage features may be degraded."
        )
        return None

    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


class StorageManager:
    """
    Manages heavy file storage (e.g., CV PDFs) using Cloudflare R2 for zero-egress, enterprise-grade edge storage.
    """

    def __init__(self):
        self.s3_client = get_s3_client()

    def upload_file(
        self,
        file_content: bytes,
        object_name: str,
        content_type: str = "application/pdf",
    ) -> str:
        """
        Uploads a file to Cloudflare R2 and returns the public/internal URL.
        """
        if not self.s3_client:
            logger.error("Cannot upload file: R2 client not initialized.")
            return ""

        try:
            self.s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=object_name,
                Body=file_content,
                ContentType=content_type,
            )
            # Assuming a custom domain or standard R2 bucket URL structure
            return f"https://{R2_BUCKET_NAME}.{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{object_name}"
        except ClientError as e:
            logger.error(f"Failed to upload file to R2: {e}")
            return ""

    def download_file(self, object_name: str) -> bytes:
        """
        Downloads a file from Cloudflare R2.
        """
        if not self.s3_client:
            logger.error("Cannot download file: R2 client not initialized.")
            return b""

        try:
            response = self.s3_client.get_object(Bucket=R2_BUCKET_NAME, Key=object_name)
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to download file from R2: {e}")
            return b""


storage_manager = StorageManager()
