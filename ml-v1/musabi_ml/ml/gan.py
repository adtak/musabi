from typing import Protocol


class GAN(Protocol):
    def fit(self):
        pass

    def predict(self):
        pass

    def save(self):
        pass
