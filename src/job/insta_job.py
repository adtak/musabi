import argparse

from typing import List

from src.bot.insta_bot import InstaBot


def main():
    args = parse_arguments()
    bot = InstaBot()

    tags = [""]
    caption = add_hashtag(args.caption, tags)

    bot.post(args.img_path, caption)


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-i", "--img_path", required=True)
    arg_parser.add_argument("-c", "--caption", required=True)
    return arg_parser.parse_args()


def add_hashtag(caption: str, tags: List[str]) -> str:
    return caption + " ".join(["#" + t for t in tags])


if __name__ == "__main__":
    main()
