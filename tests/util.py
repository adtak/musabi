import numpy as np
from typing import Tuple


def get_test_images(num: int = 1, shape: Tuple[int] = (1080, 1080, 3)):
    return [np.ones(shape=shape) for _ in range(num)]
