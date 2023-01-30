import math
import numpy as np
import os
import pathlib

from PIL import Image
from typing import List, Tuple


def resize_image(
    input_img_path: str,
    output_img_path: str,
    size: Tuple[int]
) -> None:
    img = Image.open(input_img_path)
    if img.mode == "RGB":
        resized_img = img.resize(size, Image.NEAREST)
        resized_img.save(output_img_path)


def resize_images(
    input_dir_path: str,
    output_dir_path: str,
    size: Tuple[int],
    target_suffix: List[str] = [".jpg"]
) -> None:
    prefix, suffix = "", ""

    input_dir_path = pathlib.Path(input_dir_path)
    os.makedirs(output_dir_path, exist_ok=True)
    for img_path in input_dir_path.iterdir():
        img_name = img_path.stem
        img_extension = img_path.suffix
        if img_extension in target_suffix:
            resized_img_name = f"{prefix}{img_name}{suffix}{img_extension}"
            resize_image(
                str(img_path), os.path.join(output_dir_path, resized_img_name), size
            )


def load_images(dir_path: str, target_suffix: List[str] = [".jpg"]) -> np.ndarray:
    dir_path = pathlib.Path(dir_path)
    result = []
    for i in dir_path.iterdir():
        if i.suffix in target_suffix:
            result.append(np.array(Image.open(i)))
    return np.array(result)


def save_image(img: np.ndarray, img_dir_path: str, img_name: str) -> None:
    img_dir_path = pathlib.Path(img_dir_path)
    Image.fromarray(img.astype(np.uint8)).save(
        img_dir_path / img_name
    )


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
