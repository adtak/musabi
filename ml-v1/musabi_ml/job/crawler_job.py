import argparse

import musabi_ml.util.image_util as image_util
from musabi_ml.util.crawler_util import ImageCrawler


def main():
    args = parse_arguments()
    output_dir = args.output
    ImageCrawler(output_dir).run(args.keyword, args.max)
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
