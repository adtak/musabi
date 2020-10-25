import argparse

from src.data.image_crawler import ImageCrawler
import src.util.image_util as image_util


def main():
    args = parse_arguments()
    output_dir = args.output
    _ = ImageCrawler(output_dir).run(args.keyword, args.max)
    image_util.resize_images(output_dir, args.resized_output, (1080, 1080))


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-o", "--output", required=True)
    arg_parser.add_argument("-r", "--resized_output", required=True)
    arg_parser.add_argument("-k", "--keyword", required=True)
    arg_parser.add_argument("-m", "--max", required=True, type=int)
    return arg_parser.parse_args()


if __name__ == "__main__":
    main()
