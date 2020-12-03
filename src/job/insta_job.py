import argparse
import os

from typing import List

from src.bot.insta_bot import InstaBot
from src.gan.trained_model import TrainedModel
import src.util.image_util as image_util


def main():
    args = parse_arguments()
    img_name = "gen_img.jpg"

    generate_image(args.model_dir_path, args.img_dir_path, img_name)

    tags = [""]
    caption = add_hashtag(args.caption, tags)

    bot = InstaBot()
    img_path = args.img_dir_path + "/" + img_name
    bot.post(img_path, caption)


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-m", "--model_dir_path", required=True)
    arg_parser.add_argument("-i", "--img_dir_path", required=True)
    arg_parser.add_argument("-c", "--caption")
    return arg_parser.parse_args()


def generate_image(model_dir_path: str, img_dir_path: str, img_name: str) -> None:
    model = TrainedModel(model_dir_path)
    model.load()
    img = model.predict()
    os.makedirs(img_dir_path, exist_ok=True)
    # save_image
    image_util.save_image(img[0], img_dir_path, img_name)


def add_hashtag(caption: str, tags: List[str]) -> str:
    return caption + " ".join(["#" + t for t in tags])


if __name__ == "__main__":
    main()
