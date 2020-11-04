import os

from instabot import Bot


class InstaBot(object):
    def __init__(self) -> None:
        self.bot = Bot()
        self.bot.login(username=os.environ["INSTA_USER"], password=os.environ["INSTA_PASSWORD"])

    def post(self, img_path: str, caption: str) -> None:
        self.bot.upload_photo(img_path, caption=caption)
