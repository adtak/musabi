import random
from dataclasses import dataclass
from pathlib import Path
from typing import Final, List, Optional

import numpy as np
from tensorflow.keras.layers import (Activation, BatchNormalization, Conv2D,
                                     Dense, Dropout, Flatten, LeakyReLU,
                                     Reshape, UpSampling2D)
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

from musabi_ml.ml.gan import GAN
from musabi_ml.util.image_util import save_image


@dataclass
class DCGANSetting:
    z_dim: int
    image_height: int
    image_width: int
    image_RGB: Final[int] = 3


@dataclass
class DCGANLoss:
    discriminator_loss: float
    discriminator_real_loss: float
    discriminator_fake_loss: float
    generator_loss: float


class DCGAN(GAN):
    def __init__(
        self,
    ) -> None:
        pass

    @classmethod
    def for_train(cls, settings: DCGANSetting) -> 'DCGAN':
        self = cls()
        self.settings = settings
        self.generator = create_prototype_generator(self.settings.z_dim)
        self.discriminator = create_prototype_discriminator(
            [self.settings.image_height, self.settings.image_width, self.settings.image_RGB]
        )
        self.dcgan = Sequential([self.generator, self.discriminator])
        self._compile()
        return self

    def _compile(self):
        self.discriminator.compile(
            loss="binary_crossentropy",
            optimizer=Adam(lr=1e-5, beta_1=0.1),
            metrics=["accuracy"],
        )
        self.discriminator.trainable = False
        self.dcgan.compile(
            loss="binary_crossentropy",
            optimizer=Adam(lr=2e-4, beta_1=0.5),
        )

    def fit(
        self,
        real_images: np.ndarray,  # real_images.shape => (data_size, height, width, RGB)
        batch_size: int,
        epochs: int,
        image_dir_path: Optional[Path] = None,
    ) -> List:
        losses = []
        batches = int(real_images.shape[0] / batch_size)
        for epoch in range(epochs):
            for batch in range(batches):
                real_images_batch = real_images[batch * batch_size: (batch + 1) * batch_size]

                # train discriminator
                noise = np.random.normal(0, 1, (batch_size, self.settings.z_dim))
                fake_images_batch = self.predict(noise)

                discriminator_real_loss = self.discriminator.train_on_batch(
                    real_images_batch,
                    np.array([random.uniform(0.7, 1.2) for _ in range(batch_size)]),
                )
                discriminator_fake_loss = self.discriminator.train_on_batch(
                    fake_images_batch,
                    np.array([random.uniform(0, 0.3) for _ in range(batch_size)]),
                )
                discriminator_real_loss = discriminator_real_loss[0]
                discriminator_fake_loss = discriminator_fake_loss[0]
                discriminator_loss_mean = np.add(
                    discriminator_real_loss,
                    discriminator_fake_loss,
                ) * 0.5

                # train generator
                noise = np.random.normal(0, 1, (batch_size * 2, self.settings.z_dim))
                generator_loss = self.dcgan.train_on_batch(noise, np.ones(batch_size * 2))

            losses.append(
                DCGANLoss(
                    discriminator_loss=discriminator_loss_mean,
                    discriminator_real_loss=discriminator_real_loss,
                    discriminator_fake_loss=discriminator_fake_loss,
                    generator_loss=generator_loss,
                )
            )
            self._print_loss(losses[-1], epoch)
            if image_dir_path:
                save_image(
                    fake_images_batch[0] * 127.5 + 127.5,
                    image_dir_path,
                    f"{epoch}_{batch}.jpg"
                )
        return losses

    def predict(self, noise):
        return self.generator.predict(noise)

    def save(self, output_dir_path: Path) -> None:
        self.generator.save(str(output_dir_path))

    def _print_loss(self, loss: DCGANLoss, epoch: int) -> None:
        loss_info = f"epoch: {epoch} -> " \
            f"discriminator_loss: {loss.discriminator_loss}, " \
            f"generator_loss: {loss.generator_loss}"
        print(loss_info)


def create_prototype_generator(z: int):
    noise_shape = (z,)
    model = Sequential()

    # noise_shape -> 240
    model.add(Dense(units=240, input_shape=noise_shape))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization())

    # 240 -> 240*240=57600
    model.add(Dense(240 * 240))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization())

    # 57600 -> 30*30*64
    model.add(Reshape((30, 30, 64)))

    # Upsample
    # 30*30*64 -> 180*180*64
    model.add(UpSampling2D((6, 6)))
    # 180*180*64 -> 180*180*32
    model.add(Conv2D(32, (3, 3), padding="same"))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization())

    # 180*180*32 -> 1080*1080*32
    model.add(UpSampling2D((6, 6)))
    # 1080*1080*32 -> 1080*1080*16
    model.add(Conv2D(16, (3, 3), padding="same"))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization())

    # 1080*1080*16 -> 1080*1080*3
    model.add(Conv2D(3, (3, 3), padding="same"))

    model.add(Activation("tanh"))

    return model


def create_prototype_discriminator(img_shape):
    model = Sequential()

    # 1080*1080*3 -> 540*540*64
    model.add(Conv2D(64, (3, 3), input_shape=img_shape, strides=(2, 2), padding="same"))
    model.add(LeakyReLU(0.2))

    # 540*540*64 -> 270*270*128
    model.add(Conv2D(128, (3, 3), strides=(2, 2), padding="same"))
    model.add(LeakyReLU(0.2))

    # 270*270*128 -> 135*135*256
    model.add(Conv2D(256, (3, 3), strides=(2, 2), padding="same"))
    model.add(LeakyReLU(0.2))

    # 135*135*256 -> 45*45*512
    model.add(Conv2D(512, (3, 3), strides=(3, 3), padding="same"))
    model.add(LeakyReLU(0.2))

    # 45*45*512 -> 15*15*1024
    model.add(Conv2D(1024, (3, 3), strides=(3, 3), padding="same"))
    model.add(LeakyReLU(0.2))

    # 15*15*1024 -> 230400
    model.add(Flatten())

    # 230400 -> 1024
    model.add(Dense(1024))
    model.add(LeakyReLU(0.2))
    model.add(Dropout(0.5))

    # 1024 -> 512
    model.add(Dense(512))
    model.add(LeakyReLU(0.2))
    model.add(Dropout(0.5))

    # 512 -> 256
    model.add(Dense(256))
    model.add(LeakyReLU(0.2))
    model.add(Dropout(0.5))

    # 256 -> 1
    model.add(Dense(1))
    model.add(Activation("sigmoid"))

    return model
