from src.gan.model.dcgan import DCGAN


def test_dcgan(test_images):
    dcgan = DCGAN()
    losses, gen_imgs = dcgan.train(test_images, 5)
    image_number, height, width, rgb = gen_imgs.shape

    assert len(losses) == 4
    assert image_number == 2
    assert height == 1080
    assert width == 1080
    assert rgb == 3
