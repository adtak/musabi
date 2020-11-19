from tensorflow import keras
import numpy as np


class TrainedModel(object):
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.model = None

    def load(self) -> None:
        self.model = keras.models.load_model(self.filepath)

    def predict(self):
        noise = np.random.normal(0, 1, (1, 128))
        return self.model.predict(noise)
