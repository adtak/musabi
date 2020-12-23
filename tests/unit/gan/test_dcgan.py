import math
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Reshape

import src.gan.dcgan as dcgan


def test_dcgan(monkeypatch, test_images):
    monkeypatch.setattr(dcgan, 'create_generator', mock_create_generator)
    monkeypatch.setattr(dcgan, 'create_discriminator', mock_create_discriminator)

    model = dcgan.DCGAN()
    losses, gen_imgs = model.train(test_images, 5)
    image_number, height, width, rgb = gen_imgs.shape

    assert len(losses) == 4
    assert image_number == 2
    assert height == 1080
    assert width == 1080
    assert rgb == 3


def mock_create_generator(z: int):
    input_shape = (z,)
    output_shape = (1080, 1080, 3)

    model = Sequential()
    model.add(Dense(units=math.prod(output_shape), input_shape=input_shape))
    model.add(Reshape(output_shape))

    return model


def mock_create_discriminator(img_shape):
    input_shape = img_shape
    output_shape = 1

    model = Sequential()
    model.add(Reshape((math.prod(input_shape),)))
    model.add(Dense(units=output_shape))

    return model
