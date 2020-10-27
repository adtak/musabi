import src.util.image_util as image_util


def test_load_images(test_image_dir):
    imgs = image_util.load_images(str(test_image_dir))
    num, width, height, rgb = imgs.shape
    assert num == 10
    assert width == 1080
    assert height == 1080
    assert rgb == 3
