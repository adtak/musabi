import argparse


from src.gan.trainer import Trainer


def main():
    args = parse_arguments()
    trainer = Trainer(args.train_data, args.ouput)

    trainer.train(args.epochs, args.batch_size, args.progress_interval)
    trainer.plot_loss()


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-t", "--train_data", required=True)
    arg_parser.add_argument("-o", "--output", required=True)
    arg_parser.add_argument("-e", "--epochs", required=True, type=int)
    arg_parser.add_argument("-b", "--batch_size", required=True, type=int)
    arg_parser.add_argument("-p", "--progress_interval", required=True, type=int)
    return arg_parser.parse_args()


if __name__ == "__main__":
    main()
