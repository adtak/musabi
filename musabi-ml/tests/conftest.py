from typing import Tuple

import numpy as np
import pytest
from PIL import Image


@pytest.fixture(scope="session")
def test_images():
    num: int = 10
    shape: Tuple[int] = (1080, 1080, 3)
    return np.array([np.zeros(shape=shape) for _ in range(num)], dtype="uint8")


@pytest.fixture(scope="session")
def test_image_dir(tmpdir_factory, test_images):
    dir_path = tmpdir_factory.mktemp("test_images")
    for i, img_arr in enumerate(test_images):
        fn = dir_path.join(f"image_{i}.jpg")
        Image.fromarray(img_arr).save(str(fn))
    return str(dir_path)
