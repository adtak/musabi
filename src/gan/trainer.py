import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import pathlib
import random
import seaborn as sns

from PIL import Image

import src.util.image_util as image_util
from src.gan.dcgan import DCGAN


class Trainer:
    def __init__(self, train_data_dir: str, output_dir: str):
        self.train_data_dir = pathlib.Path(train_data_dir)
        output_dir_name = datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")
        self.output_dir = pathlib.Path(output_dir) / output_dir_name
        self.output_img_dir = pathlib.Path(self.output_dir) / "generated_img"
        self.output_model_dir = pathlib.Path(self.output_dir) / "trained_model"
        os.makedirs(self.output_dir, exist_ok=False)
        os.mkdir(self.output_img_dir)
        os.mkdir(self.output_model_dir)

        self.dcgan = DCGAN()
        self.dcgan.dump_summary(self.output_dir)
        self.loss_list = []

    def train(self, epochs: int, batch_size: int) -> None:
        train_imgs = image_util.load_images(self.train_data_dir)
        batches = int(train_imgs.shape[0] / batch_size)

        print("--Train start----------------------------------")

        for epoch in range(epochs):
            train_imgs = np.array(random.sample(list(train_imgs), len(train_imgs)))
            for batch in range(batches):
                imgs = train_imgs[batch * batch_size: (batch + 1) * batch_size]
                losses, gen_imgs = self.dcgan.train(imgs, batch_size)
                self.loss_list.append(losses)
                self.show_train_progress(epoch, batch, gen_imgs[0])

    def show_train_progress(self, epoch, batch, gen_img):
        self.print_loss(epoch, batch)
        self.save_images(epoch, batch, gen_img)

    def print_loss(self, epoch, batch):
        loss = self.loss_list[-1]
        print(f"epoch: {epoch}, batch: {batch}, g_loss: {loss[0]}, d_loss: {loss[-1]}")

    # TODO: mv to util
    def save_images(self, epoch, batch, gen_img):
        Image.fromarray(gen_img.astype(np.uint8)).save(
            self.output_img_dir / f"{epoch}_{batch}.jpg"
        )

    def save_model(self):
        self.dcgan.save_model(self.output_model_dir / "trained_model")

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
