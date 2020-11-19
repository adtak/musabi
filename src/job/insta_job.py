import argparse

from typing import List

from src.bot.insta_bot import InstaBot
from src.gan.trained_model import TrainedModel
import src.util.image_util as image_util


def main():
    args = parse_arguments()
    img_name = "gen_img.jpg"

    generate_image(args.img_dir_path, img_name)

    tags = [""]
    caption = add_hashtag(args.caption, tags)

    bot = InstaBot()
    img_path = args.img_dir_path + "/" + img_name
    bot.post(img_path, caption)


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-i", "--img_dir_path", required=True)
    arg_parser.add_argument("-c", "--caption")
    return arg_parser.parse_args()


def generate_image(img_dir_path: str, img_name: str) -> None:
    model = TrainedModel()
    model.load()
    img = model.predict()
    # save_image
    image_util.save_image(img, img_dir_path, img_name)


def add_hashtag(caption: str, tags: List[str]) -> str:
    return caption + " ".join(["#" + t for t in tags])


if __name__ == "__main__":
    main()
