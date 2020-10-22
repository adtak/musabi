import numpy as np
from typing import Tuple


def get_test_images(
        num: int = 10,
        shape: Tuple[int] = (1080, 1080, 3)
) -> np.ndarray:  # no mypy stub now
    return np.array([np.ones(shape=shape) for _ in range(num)])


if __name__ == "__main__":
    pass
