from tests.util import get_test_images

from src.model.dcgan import DCGAN


def test_dcgan():
    imgs = get_test_images()
    dcgan = DCGAN()
    losses, gen_imgs = dcgan.train(imgs, 5)
    image_number, height, width, rgb = gen_imgs.shape

    assert len(losses) == 4
    assert image_number == 2
    assert height == 1080
    assert width == 1080
    assert rgb == 3


if __name__ == "__main__":
    test_dcgan()
