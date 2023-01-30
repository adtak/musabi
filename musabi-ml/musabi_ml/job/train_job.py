import argparse

from musabi_ml.ml.trainer import Trainer


def main():
    args = parse_arguments()
    trainer = Trainer(args.input_dir, args.output_dir)
    trainer.train(args.batch_size, args.epochs)
    trainer.plot_loss()
    trainer.save_model()


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-i', '--input_dir', default='datasets')
    arg_parser.add_argument('-o', '--output_dir', default='train_results')
    arg_parser.add_argument('-b', '--batch_size', required=True, type=int)
    arg_parser.add_argument('-e', '--epochs', required=True, type=int)
    return arg_parser.parse_args()


if __name__ == "__main__":
    main()
