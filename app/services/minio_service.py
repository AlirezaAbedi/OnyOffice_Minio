from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class MinioService:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        protocol = "https" if secure else "http"
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=f"{protocol}://{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchBucket"}:
                self.client.create_bucket(Bucket=self.bucket)
            else:
                raise

    def upload_fileobj(self, fileobj: BinaryIO, object_name: str, content_type: str) -> None:
        self.client.upload_fileobj(
            fileobj,
            self.bucket,
            object_name,
            ExtraArgs={"ContentType": content_type},
        )

    def upload_bytes(self, data: bytes, object_name: str, content_type: str) -> None:
        self.upload_fileobj(BytesIO(data), object_name, content_type)

    def download_bytes(self, object_name: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=object_name)
        return response["Body"].read()

    def delete(self, object_name: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=object_name)

    def presigned_get_url(self, object_name: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_name},
            ExpiresIn=expires_in,
        )
