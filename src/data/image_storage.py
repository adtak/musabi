import boto3
import os


class ImageStorage(object):
    def __init__(self) -> None:
        self.s3 = boto3.resource("s3")
        self.bucket_name = os.environ["AWS_S3_BUCKET"]

    def push_images(self, output_dir, images) -> None:
        for image in images:
            self.s3.meta.client.upload_file(
                output_dir + "/" + image, self.bucket_name, image)


if __name__ == "__main__":
    pass
