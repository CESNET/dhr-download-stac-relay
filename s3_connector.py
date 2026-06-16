from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError


class S3Connector:
    def __init__(
            self,
            host_base: str,
            access_key: str,
            secret_key: str,
            host_bucket: str,
            logger,
            service_name: str = "s3",
    ):
        self._logger = logger
        self._bucket = host_bucket

        self._s3_client = boto3.client(
            service_name=service_name,
            endpoint_url=host_base,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        self._logger.debug(f"S3 client initialized for bucket={host_bucket} endpoint={host_base}")

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def client(self):
        return self._s3_client

    def upload_file(self, local_file: str | Path, bucket_key: str) -> None:
        local_file = Path(local_file)

        self._logger.info(f"Uploading file={local_file} to key={bucket_key}")

        try:
            self._s3_client.upload_file(str(local_file), self._bucket, bucket_key)

        except ClientError:
            self._logger.exception(f"Upload failed for key={bucket_key}")
            raise

    def download_file(self, path: str | Path, bucket_key: str) -> None:
        path = Path(path)

        self._logger.info(f"Downloading key={bucket_key} into file={path}")

        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._s3_client.download_file(self._bucket, bucket_key, str(path))

        except ClientError:
            self._logger.exception(f"Download failed for key={bucket_key}")
            raise

    def delete_key(self, bucket_key: str) -> None:
        try:
            self._s3_client.delete_object(Bucket=self._bucket, Key=bucket_key)

        except ClientError:
            self._logger.exception(f"Delete failed for key={bucket_key}")
            raise

    def key_exists(self, bucket_key: str, expected_length: int | None = None) -> bool:
        try:
            metadata = self._s3_client.head_object(
                Bucket=self._bucket,
                Key=bucket_key,
            )

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in ("404", "NoSuchKey"):
                return False

            raise

        if expected_length is None:
            return True

        actual_length = metadata["ContentLength"]

        if actual_length != expected_length:
            self._logger.warning(
                f"Key={bucket_key} size mismatch (actual: {actual_length} != expected: {expected_length})"
            )
            return False

        return True

    def list_files(self, prefix: str) -> list[str]:
        try:
            response = self._s3_client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=prefix.rstrip("/") + "/",
            )

        except ClientError:
            self._logger.exception(f"List failed for prefix={prefix}")
            return []

        return [obj["Key"] for obj in response.get("Contents", [])]

    def get_file_object(self, key: str):
        return self._s3_client.get_object(
            Bucket=self._bucket,
            Key=key,
        )

    def fetch_range_from_tar(self, key: str, offset: int, size: int) -> BinaryIO:
        byte_range = f"bytes={offset}-{offset + size - 1}"

        response = self._s3_client.get_object(
            Bucket=self._bucket,
            Key=key,
            Range=byte_range,
        )

        return response["Body"]

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self._s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
            },
            ExpiresIn=expires_in,
        )

    def head_object(self, key: str) -> dict:
        return self._s3_client.head_object(Bucket=self._bucket, Key=key)
