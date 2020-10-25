import argparse

from src.data.image_crawler import ImageCrawler


def main():
    args = parse_arguments()
    output_dir = args.output
    _ = ImageCrawler(output_dir).run(args.keyword, args.max)


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-o", "--output", required=True)
    arg_parser.add_argument("-k", "--keyword", required=True)
    arg_parser.add_argument("-m", "--max", required=True, type=int)
    return arg_parser.parse_args()


if __name__ == "__main__":
    main()
