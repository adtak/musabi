import os
import random
from datetime import datetime
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

import musabi_ml.util.image_util as image_util
from musabi_ml.ml.dcgan import DCGAN, DCGANLoss, DCGANSetting


class Trainer(object):
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        output_dir_name = datetime.now().strftime("%Y%m%d_%H_%M_%S")
        self.output_dir = Path(output_dir) / output_dir_name
        self.output_img_dir = Path(self.output_dir) / "generated_img"
        self.output_model_dir = Path(self.output_dir) / "trained_model"
        os.makedirs(self.output_dir, exist_ok=False)
        os.mkdir(self.output_img_dir)
        os.mkdir(self.output_model_dir)

        self.settings = DCGANSetting(128, 1080, 1080)
        self.dcgan = DCGAN.for_train(self.settings)
        self.loss_list: List[DCGANLoss] = None

    def train(self, batch_size: int, epochs: int) -> None:
        print("--Train start----------------------------------")

        train_imgs = image_util.load_images(self.input_dir)
        train_imgs = np.array(random.sample(list(train_imgs), len(train_imgs)))
        losses = self.dcgan.fit(train_imgs, batch_size, epochs, self.output_img_dir)
        self.loss_list = losses

        print("--Train end----------------------------------")

    def save_model(self):
        self.dcgan.save(self.output_model_dir)

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

        plt.savefig(self.output_dir / "loss.jpg")
