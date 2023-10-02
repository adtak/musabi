import numpy as np
import pytest

import musabi_bot.util.image_util as image_util


def test_resize_images(
    tmpdir_factory: pytest.TempdirFactory, test_images: np.ndarray, test_image_dir: str
) -> None:
    # setting
    size = (256, 256)
    output_dir_path = tmpdir_factory.mktemp("test_resized_images")
    # run target function
    image_util.resize_images(test_image_dir, output_dir_path, size)
    # check result
    resized_imgs = image_util.load_images(str(output_dir_path))
    expected_size = size
    actual_size = resized_imgs.shape[1:3]  # (num, width, height, rgb)

    assert len(test_images) == len(resized_imgs)
    assert expected_size == actual_size


def test_load_images(test_image_dir: str) -> None:
    imgs = image_util.load_images(test_image_dir)
    num, width, height, rgb = imgs.shape

    assert num == 10
    assert width == 1080
    assert height == 1080
    assert rgb == 3
