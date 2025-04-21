import os
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile


def load_images(
    dir_path: Path,
    target_suffix: Tuple[str] = ('.jpg'),
) -> List[JpegImageFile]:
    return [
        Image.open(i) for i in dir_path.iterdir() if i.suffix != '' and i.suffix in target_suffix]


def load_images_as_array(
    dir_path: Path,
) -> np.ndarray:
    return np.array([np.array(i) for i in load_images(dir_path)])


def save_image_from_array(
    image: np.ndarray,
    dir_path: Path,
    image_name: str,
) -> None:
    Image.fromarray(image.astype(np.uint8)).save(dir_path / image_name)


def expand2square(image: JpegImageFile, background_color: Tuple[int, int, int]) -> Image.Image:
    width, height = image.size
    if width == height:
        result = Image.new(image.mode, (width, height), background_color)
        result.paste(image, (0, 0))
    elif width > height:
        result = Image.new(image.mode, (width, width), background_color)
        result.paste(image, (0, (width - height) // 2))
    else:
        result = Image.new(image.mode, (height, height), background_color)
        result.paste(image, ((height - width) // 2, 0))
    return result


def resize_image(
    image: JpegImageFile,
    size: Tuple[int],
    background_color: Tuple[int],
) -> Image.Image:
    return expand2square(image, background_color).resize(size, Image.NEAREST)


def save_resize_images(
    input_dir_path: Path,
    output_dir_path: Path,
    size: Tuple[int],
    background_color: Tuple[int] = (256, 256, 256),
) -> None:
    os.makedirs(output_dir_path, exist_ok=True)
    images = load_images(input_dir_path, ('.jpg'))
    for image in images:
        filename = Path(image.filename).name
        resized_image = resize_image(image, size, background_color)
        output_file_path = output_dir_path / f'resized_{filename}'
        resized_image.save(output_file_path)
