import numpy as np

from src.gan.trainer import Trainer
from src.gan.dcgan import DCGAN


def test_trainer(tmpdir_factory, monkeypatch, test_image_dir):
    # mock
    monkeypatch.setattr(DCGAN, "__init__", lambda x: None)
    monkeypatch.setattr(DCGAN, "train", mock_train)
    monkeypatch.setattr(DCGAN, "dump_summary", lambda x, y: None)
    # setting
    output_dir_path = tmpdir_factory.mktemp("test_output")
    # run trainer
    trainer = Trainer(test_image_dir, output_dir_path)
    trainer.train(1, 5, 1)
    trainer.plot_loss()
    # check
    assert len(trainer.loss_list) == 2
    for losses in trainer.loss_list:
        assert losses == tuple([0.5]*4)


def mock_train(self, imgs, batch_size):
    return tuple([0.5]*4), np.zeros((batch_size, 1080, 1080, 3), dtype="uint8")
