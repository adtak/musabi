import datetime
import matplotlib.pyplot as plt
import numpy as np
import math
import os
import random
import seaborn as sns

from keras.datasets import cifar10
from PIL import Image

from src.model.dcgan import DCGAN


class Trainer():
    def __init__(self, epochs, batch_size, show_progress_interval):
        self.working_dir = "./report/" + datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S") + "/"
        self.epochs = epochs
        self.batch_size = batch_size
        self.show_progress_interval = show_progress_interval

        if not os.path.exists(self.working_dir):
            os.mkdir(self.working_dir)
        else:
            raise Exception

        self.dcgan = DCGAN()
        self.dcgan.dump_summary(self.working_dir)
        self.losses_list = []

    def train(self, train_name):
        train_imgs = self.load_images(train_name)
        num_batches = int(train_imgs.shape[0]/self.batch_size)

        print("Train start----------------------------------")
        print("Num of Batches: ", num_batches)
        print("---------------------------------------------")

        for epoch in range(self.epochs):
            train_imgs = np.array(random.sample(list(train_imgs), len(train_imgs)))
            for batch_idx in range(num_batches):
                imgs = train_imgs[batch_idx*self.batch_size: (batch_idx+1)*self.batch_size]
                losses, gen_imgs = self.dcgan.train(imgs, self.batch_size)
                self.losses_list.append(losses)

                if batch_idx % self.show_progress_interval == 0:
                    self.dump_train_progress(epoch, batch_idx, gen_imgs)

    def load_images(self, img_name):
        if img_name == "cifar10":
            (img, _), (_, _) = cifar10.load_data()
        else:
            raise Exception

        return img[:100]

    def dump_train_progress(self, epoch, batch_idx, gen_imgs):
        self.print_loss(epoch, batch_idx)
        self.dump_images(epoch, batch_idx, gen_imgs)

    def print_loss(self, epoch, batch_idx):
        losses = self.losses_list[-1]
        print("epoch: %d, batch: %d, g_loss: %f, d_loss: %f" % (epoch, batch_idx, losses[0], losses[-1]))

    def dump_images(self, epoch, batch_idx, gen_imgs):
        img_dir = self.working_dir + "generated_img/"
        if not os.path.exists(img_dir):
            os.mkdir(img_dir)

        images = combine_images(gen_imgs)
        Image.fromarray(images.astype(np.uint8)).save(img_dir + "%04d_%04d.png" % (epoch, batch_idx))

    def dump_model(self):
        self.dcgan.dump_model(self.working_dir)

    def plot_loss(self):
        losses_array = np.array(self.losses_list).T

        sns.set_style("whitegrid")
        _, ax = plt.subplots(figsize=(15, 5))

        ax.plot(losses_array[0], label="Discriminator_Loss")
        ax.plot(losses_array[-1], label="Generator_Loss")

        ax.set_xlabel("Iteration")
        ax.set_ylabel("Loss")
        ax.legend()

        plt.savefig(self.working_dir + "loss.png", box_inches=0.1)


def combine_images(images):
    # 枚数*縦*横*RGB
    # imageの枚数
    total = images.shape[0]
    cols = int(math.sqrt(total))
    rows = math.ceil(float(total)/cols)

    width, height, rgb = images.shape[1:]
    combined_image = np.zeros((rows*height, cols*width, rgb), dtype=images.dtype)

    # 縦*横*RGB
    for image_idx, image in enumerate(images):
        i = int(image_idx/cols)
        j = image_idx % cols

        # 縦*横
        for rgb_idx in range(image.shape[-1]):
            combined_image[width*i:width*(i+1), height*j:height*(j+1), rgb_idx] = image[:, :, rgb_idx]

    return combined_image


if __name__ == "__main__":
    trainer = Trainer(
        epochs=1,
        batch_size=10,
        show_progress_interval=1)

    trainer.train("cifar10")
    trainer.plot_loss()
