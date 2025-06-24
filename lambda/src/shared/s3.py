import io

import boto3
from PIL import Image


def get_image(bucket_name: str, s3_object_key: str) -> Image.Image:
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=s3_object_key)
    image_bytes = response["Body"].read()
    return Image.open(io.BytesIO(image_bytes))


def put_image(image: Image.Image, bucket_name: str, s3_object_key: str) -> str:
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_object_key,
        Body=image_buffer,
        ContentType="image/png",
    )
    return s3_object_key
