import keras


class ModelLoader(object):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.model = None

    def load(self):
        self.model = keras.models.load_model(self.filepath)
