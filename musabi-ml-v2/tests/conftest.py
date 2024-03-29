from typing import Tuple

import numpy as np
import py
import pytest
from PIL import Image


@pytest.fixture(scope="session")
def test_images() -> np.ndarray:
    num: int = 10
    shape: Tuple[int, int, int] = (1080, 1080, 3)
    return np.array([np.zeros(shape=shape) for _ in range(num)], dtype="uint8")


@pytest.fixture(scope="session")
def test_image_dir(
    tmpdir_factory: pytest.TempdirFactory, test_images: np.ndarray
) -> str:
    dir_path: py.path.local = tmpdir_factory.mktemp("test_images")
    for i, img_arr in enumerate(test_images):
        fn = dir_path.join(f"image_{i}.jpg")
        Image.fromarray(img_arr).save(str(fn))
    return str(dir_path)
