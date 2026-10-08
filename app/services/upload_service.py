import logging
import os

import aioboto3
import boto3
import aiohttp
from fastapi import HTTPException

from app.core.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UploadService:
    def __init__(self):
        self.s3_session = aioboto3.Session()
        # Hosting environment values take precedence over legacy defaults.
        self.s3_bucket_name = os.getenv("AWS_BUCKET_NAME") or settings.AWS_BUCKET_NAME
        self.s3_region = os.getenv("AWS_REGION") or settings.AWS_REGION
        self.s3_access_key = os.getenv("AWS_ACCESS_KEY_ID") or settings.AWS_ACCESS_KEY_ID
        self.s3_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or settings.AWS_SECRET_ACCESS_KEY
        logger.info(
            f"Initialized UploadService with bucket: {self.s3_bucket_name} in region: {self.s3_region}"
        )

    async def upload_to_s3(
        self,
        file_content: bytes,
        destination_path: str,
        content_type: str | None = None,
    ) -> str:
        """
        Upload file to AWS S3 bucket and return its public URL

        Args:
            file_content: Raw bytes of the file
            destination_path: Path/key where file will be stored in S3
            content_type: MIME type of the file (optional)

        Returns:
            str: Public URL of the stored file
        """
        try:
            logger.info(f"Attempting to upload file to S3: {destination_path}")
            logger.info(f"Content type: {content_type}")
            logger.info(f"File size: {len(file_content)} bytes")
            logger.info(f"Using AWS region: {self.s3_region}")
            logger.info(f"Using AWS bucket: {self.s3_bucket_name}")

            async with self.s3_session.client(
                "s3",
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region,
                endpoint_url=f"https://s3.{self.s3_region}.amazonaws.com",
            ) as s3:
                # PutObject can work without the ListBucket permission required by head_bucket.
                await s3.put_object(
                    Bucket=self.s3_bucket_name,
                    Key=destination_path,
                    Body=file_content,
                    ContentType=content_type or "application/octet-stream",
                )

                file_url = f"https://{self.s3_bucket_name}.s3.{self.s3_region}.amazonaws.com/{destination_path}"
                logger.info(f"Successfully uploaded file to S3: {file_url}")
                return file_url

        except Exception as e:
            logger.error(f"S3 upload operation failed: {str(e)}")
            raise HTTPException(
                status_code=503, detail="File storage is temporarily unavailable"
            )

    def upload_file(
        self,
        file_content: bytes,
        destination_path: str,
        content_type: str | None = None,
    ) -> str:
        """
        Upload file to AWS S3 bucket and return its public URL (synchronous)

        Args:
            file_content: Raw bytes of the file
            destination_path: Path/key where file will be stored in S3
            content_type: MIME type of the file (optional)

        Returns:
            str: Public URL of the stored file
        """
        try:
            logger.info(f"Attempting to upload file to S3 (sync): {destination_path}")
            logger.info(f"Content type: {content_type}")
            logger.info(f"File size: {len(file_content)} bytes")
            logger.info(f"Using AWS region: {self.s3_region}")
            logger.info(f"Using AWS bucket: {self.s3_bucket_name}")

            s3 = boto3.client(
                "s3",
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region,
                endpoint_url=f"https://s3.{self.s3_region}.amazonaws.com",
            )

            # Check bucket
            try:
                logger.info(f"Checking if bucket {self.s3_bucket_name} exists (sync)...")
                s3.head_bucket(Bucket=self.s3_bucket_name)
                logger.info("Bucket exists and is accessible (sync)")
            except Exception as bucket_error:
                logger.error(f"Bucket check failed (sync): {str(bucket_error)}")
                raise HTTPException(status_code=500, detail=f"S3 bucket check failed: {str(bucket_error)}")

            # Upload
            s3.put_object(
                Bucket=self.s3_bucket_name,
                Key=destination_path,
                Body=file_content,
                ContentType=content_type or "application/octet-stream",
            )

            file_url = f"https://{self.s3_bucket_name}.s3.{self.s3_region}.amazonaws.com/{destination_path}"
            logger.info(f"Successfully uploaded file to S3 (sync): {file_url}")
            return file_url
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"S3 upload operation failed (sync): {str(e)}")
            raise HTTPException(status_code=503, detail="File storage is temporarily unavailable")

    async def delete_from_s3(self, s3_key: str) -> bool:
        """
        Delete a file from AWS S3 by object key
        """
        try:
            async with self.s3_session.client(
                "s3",
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region,
                endpoint_url=f"https://s3.{self.s3_region}.amazonaws.com",
            ) as s3:
                await s3.delete_object(Bucket=self.s3_bucket_name, Key=s3_key)
                logger.info(f"Deleted S3 object: {s3_key}")
                return True
        except Exception as e:
            logger.error(f"S3 delete failed: {str(e)}")
            return False

    async def download_from_s3(self, s3_key: str) -> bytes:
        """Fetch a private document for an authorized backend request."""
        try:
            async with self.s3_session.client(
                "s3",
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region,
                endpoint_url=f"https://s3.{self.s3_region}.amazonaws.com",
            ) as s3:
                response = await s3.get_object(Bucket=self.s3_bucket_name, Key=s3_key)
                async with response["Body"] as body:
                    return await body.read()
        except Exception:
            raise HTTPException(status_code=502, detail="Document storage unavailable")

# Create a singleton instance
upload_service = UploadService()
