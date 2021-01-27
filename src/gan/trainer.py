import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import pathlib
import random
import seaborn as sns
from typing import List

import src.util.image_util as image_util
from src.gan.dcgan import DCGAN, DCGANLoss


class Trainer(object):
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
        self.loss_list: List[DCGANLoss] = []

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

        self.save_model()

        print("--Train end----------------------------------")

    def show_train_progress(self, epoch, batch, gen_img):
        self.print_loss(epoch, batch)
        self.save_image(epoch, batch, gen_img)

    def print_loss(self, epoch, batch):
        loss: DCGANLoss = self.loss_list[-1]
        loss_str = f"epoch: {epoch}, batch: {batch}, " \
            f"discriminator_loss: {loss.discriminator_loss}," \
            f"generator_loss: {loss.generator_loss}"
        print(loss_str)

    def save_image(self, epoch, batch, gen_img):
        image_util.save_image(gen_img, self.output_img_dir, f"{epoch}_{batch}.jpg")

    def save_model(self):
        self.dcgan.save_generator(self.output_model_dir / "trained_model")

    def plot_loss(self):
        discriminator_losses = np.array([loss.discriminator_loss for loss in self.loss_list])
        generator_losses = np.array([loss.generator_loss for loss in self.loss_list])

        sns.set_style("whitegrid")
        _, ax = plt.subplots(figsize=(15, 5))

        ax.plot(discriminator_losses, label="Discriminator_Loss")
        ax.plot(generator_losses, label="Generator_Loss")

        ax.set_xlabel("Iteration")
        ax.set_ylabel("Loss")
        ax.legend()

        plt.savefig(self.output_dir / "loss.jpg", box_inches=0.1)
