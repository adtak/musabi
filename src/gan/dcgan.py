import numpy as np
import random

from keras.models import Sequential
from keras.layers import Dense, Activation, Reshape, Flatten, Dropout, UpSampling2D
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv2D
from keras.layers.advanced_activations import LeakyReLU
from keras.optimizers import Adam


def create_generator(z: int = 128):
    noise_shape = (z,)
    model = Sequential()

    # noise_shape -> 240
    model.add(Dense(units=240, input_shape=noise_shape))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization())

    # 240 -> 240*240=57600
    model.add(Dense(240*240))
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


def create_discriminator(img_shape):
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


class DCGAN():
    def __init__(self, img_shape=(1080, 1080, 3), z_dim=128) -> None:
        self.img_shape = img_shape
        self.z_dim = z_dim

        self.generator = self._create_generator(self.z_dim)
        self.discriminator = self._create_discriminator(self.img_shape)
        self.dcgan = self._create_dcgan()

        d_opt = Adam(lr=1e-5, beta_1=0.1)
        self.discriminator.compile(
            loss="binary_crossentropy", optimizer=d_opt, metrics=["accuracy"])
        self.discriminator.trainable = False

        dcgan_opt = Adam(lr=2e-4, beta_1=0.5)
        self.dcgan.compile(loss="binary_crossentropy", optimizer=dcgan_opt)

    def _create_generator(self, z_dim):
        return create_generator(z_dim)

    def _create_discriminator(self, img_shape):
        return create_discriminator(img_shape)

    def _create_dcgan(self):
        return Sequential([self.generator, self.discriminator])

    def train(self, imgs, batch_size):
        imgs = (imgs.astype(np.float32)-127.5)/127.5

        # train discriminator
        half_batch_size = int(batch_size/2)
        noise = np.random.normal(0, 1, (half_batch_size, self.z_dim))
        gen_imgs = self.generate_image(noise)

        idx = np.random.randint(0, imgs.shape[0], half_batch_size)
        imgs = imgs[idx]

        # soft label
        d_loss_real = self.discriminator.train_on_batch(
            imgs,
            np.array([random.uniform(0.7, 1.2) for _ in range(half_batch_size)]))
        d_loss_fake = self.discriminator.train_on_batch(
            gen_imgs,
            np.array([random.uniform(0, 0.3) for _ in range(half_batch_size)]))

        d_loss_real = d_loss_real[0]
        d_loss_fake = d_loss_fake[0]
        d_loss = np.add(d_loss_real, d_loss_fake)*0.5

        # train generator
        noise = np.random.normal(0, 1, (batch_size, self.z_dim))
        g_loss = self.dcgan.train_on_batch(noise, np.array([1]*batch_size))

        # cross entropyを使っているので、- (t * log(D(G(z))) + (1-t) * log(1 - D(G(z))))がLossだが、
        # soft1なLabelにして1でなくなると、第2項が残っちゃうので、t * log(D(G(z)))を最大化できなくなる
        # ちなみに論文にはlog(1 - D(G(z)))を最小化すると書いてあるが、勾配消失しやすいので
        # 実用的にはlog(D(G(z)))を最大化するべきらしい
        gen_imgs = gen_imgs * 127.5 + 127.5

        return (d_loss, d_loss_real, d_loss_fake, g_loss), gen_imgs

    def generate_image(self, noise):
        return self.generator.predict(noise)

    def dump_summary(self, root_path):
        with open(root_path+"generator_report.txt", "w") as fh:
            self.generator.summary(print_fn=lambda x: fh.write(x+"¥n"))
        with open(root_path+"discriminator_report.txt", "w") as fh:
            self.discriminator.summary(print_fn=lambda x: fh.write(x+"¥n"))

    def dump_model(self):
        pass


if __name__ == "__main__":
    pass
