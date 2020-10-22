from tests.util import get_test_images

from src.model.dcgan import DCGAN


def test_dcgan():
    imgs = get_test_images()
    dcgan = DCGAN()
    losses, gen_imgs = dcgan.train(imgs, 1)


if __name__ == "__main__":
    test_dcgan()
