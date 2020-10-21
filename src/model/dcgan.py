import numpy as np
import random

from keras.models import Sequential
from keras.layers import Dense, Activation, Reshape, Flatten, Dropout, UpSampling2D
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv2D
from keras.layers.advanced_activations import LeakyReLU
from keras.optimizers import Adam


def create_my_generator(z_dim):
    noise_shape = (z_dim,)
    model = Sequential()

    # noise_shape -> 1024
    model.add(Dense(units=1024, input_shape=noise_shape))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization())

    # 1024 -> 1024*64=65536
    model.add(Dense(1024*64))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization())

    # 65536 -> 8*8*1024
    model.add(Reshape((8, 8, 1024)))

    # Upsample
    # 8*8*1024 -> 16*16*1024
    model.add(UpSampling2D((2, 2)))
    # 16*16*1024 -> 16*16*512
    model.add(Conv2D(512, (3, 3), padding="same"))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization())

    # 16*16*512 -> 32*32*512
    model.add(UpSampling2D((2, 2)))

    # 32*32*512 -> 32*32*3
    model.add(Conv2D(3, (3, 3), padding="same"))

    # 32*32*512 -> 32*32*256
    # model.add(Conv2D(256, (3, 3), padding="same"))
    # model.add(LeakyReLU(0.2))
    # model.add(BatchNormalization())

    # # 32*32*256 -> 64*64*256
    # model.add(UpSampling2D((2, 2)))
    # # 64*64*256 -> 64*64*128
    # model.add(Conv2D(128, (3, 3), padding="same"))
    # model.add(LeakyReLU(0.2))
    # model.add(BatchNormalization())

    # # 64*64*128 -> 128*128*128
    # model.add(UpSampling2D((2, 2)))
    # # 128*128*128 -> 128*128*64
    # model.add(Conv2D(64, (3, 3), padding="same"))
    # model.add(LeakyReLU(0.2))
    # model.add(BatchNormalization())

    # # 128*128*64 -> 128*128*3
    # model.add(Conv2D(3, (3, 3), padding="same"))

    model.add(Activation("tanh"))

    return model


def create_my_discriminator(img_shape):
    model = Sequential()

    # 128*128*3 -> 64*64*64
    # model.add(Conv2D(64, (3, 3), input_shape=img_shape, strides=(2, 2), padding="same"))
    # model.add(LeakyReLU(0.2))

    # # 64*64*64 -> 32*32*128
    # model.add(Conv2D(128, (3, 3), strides=(2, 2), padding="same"))
    # model.add(LeakyReLU(0.2))

    # 32*32*3 -> 16*16*64
    model.add(Conv2D(64, (3, 3), input_shape=img_shape, strides=(2, 2), padding="same"))
    model.add(LeakyReLU(0.2))

    # # 16*16*64 -> 8*8*128
    model.add(Conv2D(128, (3, 3), strides=(2, 2), padding="same"))
    model.add(LeakyReLU(0.2))

    # 8*8*128 -> 8192
    model.add(Flatten())

    # 8192 -> 256
    model.add(Dense(256))
    model.add(LeakyReLU(0.2))
    model.add(Dropout(0.5))

    # 256 -> 1
    model.add(Dense(1))
    model.add(Activation("sigmoid"))

    return model


class DCGAN():
    def __init__(self, is_load=False, time_str=None):
        if is_load:
            pass
        else:
            self.IMG_SHAPE = (32, 32, 3)
            self.Z_DIM = 128
            self.RGB_VAL = 256

            self.generator = self.create_generator(self.Z_DIM)
            self.discriminator = self.create_discriminator(self.IMG_SHAPE)
            self.dcgan = self.create_dcgan()

            d_opt = Adam(lr=1e-5, beta_1=0.1)
            self.discriminator.compile(
                loss="binary_crossentropy", optimizer=d_opt, metrics=["accuracy"])

            self.discriminator.trainable = False
            dcgan_opt = Adam(lr=2e-4, beta_1=0.5)
            self.dcgan.compile(loss="binary_crossentropy", optimizer=dcgan_opt)

    def create_generator(self, z_dim):
        return create_my_generator(z_dim)

    def create_discriminator(self, img_shape):
        return create_my_discriminator(img_shape)

    def create_dcgan(self):
        return Sequential([self.generator, self.discriminator])

    def train(self, imgs, batch_size):
        imgs = (imgs.astype(np.float32)-127.5)/127.5

        # train discriminator
        half_batch_size = int(batch_size/2)
        noise = np.random.normal(0, 1, (half_batch_size, self.Z_DIM))
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
        noise = np.random.normal(0, 1, (batch_size, self.Z_DIM))
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

    def dump_model(self, root_path):
        pass


if __name__ == "__main__":
    pass
