import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import pathlib
import random
import seaborn as sns

from PIL import Image

import src.util.image_util as image_util
from src.gan.model.dcgan import DCGAN


class Trainer:
    def __init__(self, train_data_dir: str, output_dir: str):
        self.train_data_dir = pathlib.Path(train_data_dir)
        output_dir_name = datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")
        self.output_dir = pathlib.Path(output_dir) / output_dir_name
        os.makedirs(self.output_dir, exist_ok=False)

        self.dcgan = DCGAN()
        self.dcgan.dump_summary(self.output_dir)
        self.loss_list = []

    def train(self, epochs, batch_size, show_progress_interval):
        train_imgs = image_util.load_images(self.train_data_dir)
        num_batches = int(train_imgs.shape[0] / batch_size)

        print("Train start----------------------------------")
        print("Num of Batches: ", num_batches)
        print("---------------------------------------------")

        for epoch in range(epochs):
            train_imgs = np.array(random.sample(list(train_imgs), len(train_imgs)))
            for batch_idx in range(num_batches):
                imgs = train_imgs[batch_idx * batch_size: (batch_idx + 1) * batch_size]
                losses, gen_imgs = self.dcgan.train(imgs, batch_size)
                self.loss_list.append(losses)

                if batch_idx % show_progress_interval == 0:
                    self.dump_train_progress(epoch, batch_idx, gen_imgs[0])

    def dump_train_progress(self, epoch, batch_idx, gen_img):
        self.print_loss(epoch, batch_idx)
        self.dump_images(epoch, batch_idx, gen_img)

    def print_loss(self, epoch, batch_idx):
        losses = self.loss_list[-1]
        print(
            "epoch: %d, batch: %d, g_loss: %f, d_loss: %f"
            % (epoch, batch_idx, losses[0], losses[-1])
        )

    def dump_images(self, epoch, batch_idx, gen_img):
        img_dir = self.output_dir / "generated_img"
        if not os.path.exists(img_dir):
            os.mkdir(img_dir)

        Image.fromarray(gen_img.astype(np.uint8)).save(
            img_dir / f"{epoch}_{batch_idx}.jpg"
        )

    def dump_model(self):
        self.dcgan.dump_model(self.output_dir)

    def plot_loss(self):
        losses_array = np.array(self.loss_list).T

        sns.set_style("whitegrid")
        _, ax = plt.subplots(figsize=(15, 5))

        ax.plot(losses_array[0], label="Discriminator_Loss")
        ax.plot(losses_array[-1], label="Generator_Loss")

        ax.set_xlabel("Iteration")
        ax.set_ylabel("Loss")
        ax.legend()

        plt.savefig(self.output_dir / "loss.jpg", box_inches=0.1)
