import numpy as np
from src.gan.dcgan import DCGAN, DCGANLoss
from src.gan.trainer import Trainer


def test_trainer(tmpdir_factory, monkeypatch, test_image_dir):
    # mock
    monkeypatch.setattr(DCGAN, "__init__", lambda x: None)
    monkeypatch.setattr(DCGAN, "train", mock_train)
    monkeypatch.setattr(DCGAN, "dump_summary", lambda x, y: None)
    monkeypatch.setattr(DCGAN, "save_generator", lambda x, y: None)
    # setting
    output_dir_path = tmpdir_factory.mktemp("test_output")
    # run trainer
    trainer = Trainer(test_image_dir, output_dir_path)
    trainer.train(1, 5)
    trainer.plot_loss()
    # check
    assert len(trainer.loss_list) == 2
    for losses in trainer.loss_list:
        assert losses.discriminator_loss == 0.1
        assert losses.discriminator_real_loss == 0.2
        assert losses.discriminator_fake_loss == 0.3
        assert losses.generator_loss == 0.4


def mock_train(self, imgs, batch_size):
    return DCGANLoss(
        discriminator_loss=0.1,
        discriminator_real_loss=0.2,
        discriminator_fake_loss=0.3,
        generator_loss=0.4
    ), np.zeros((batch_size, 1080, 1080, 3), dtype="uint8")
