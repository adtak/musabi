import math
import numpy as np
import os
import pathlib

from PIL import Image
from typing import Tuple


def resize_image(input_img_path: str, output_img_path: str, size: Tuple[int]) -> None:
    img = Image.open(input_img_path)
    if img.mode == "RGB":
        resized_img = img.resize(size, Image.NEAREST)
        resized_img.save(output_img_path)


def resize_images(input_dir_path: str, output_dir_path: str, size: Tuple[int]) -> None:
    prefix, suffix = "", ""

    input_dir_path = pathlib.Path(input_dir_path)
    os.mkdirs(output_dir_path, exist_ok=True)
    for img_path in input_dir_path.iterdir():
        img_name = img_path.stem
        img_extension = img_path.suffix
        if img_path.suffix in [".jpg"]:
            resized_img_name = f"{prefix}{img_name}{suffix}{img_extension}"
            resize_image(str(img_path), os.path.join(output_dir_path, resized_img_name), size)


def load_images(dir_path: str) -> np.ndarray:
    dir_path = pathlib.Path(dir_path)
    result = []
    for i in dir_path.iterdir():
        if i.suffix in [".jpg"]:
            result.append(np.array(Image.open(i)))
    return np.array(result)


def combine_images(imgs):
    # imgs.shape = 枚数*縦*横*RGB
    total = imgs.shape[0]
    cols = int(math.sqrt(total))
    rows = math.ceil(float(total) / cols)

    width, height, rgb = imgs.shape[1:]
    combined_image = np.zeros((rows * height, cols * width, rgb), dtype=imgs.dtype)

    # 縦*横*RGB
    for image_idx, image in enumerate(imgs):
        i = int(image_idx / cols)
        j = image_idx % cols

        # 縦*横
        for rgb_idx in range(image.shape[-1]):
            combined_image[
                width * i: width * (i + 1), height * j: height * (j + 1), rgb_idx
            ] = image[:, :, rgb_idx]

    return combined_image


if __name__ == "__main__":
    resize_images("./data/raw_data", "./data/edit_data", (1080, 1080))
