import os
import traceback
import urllib
from pathlib import Path
from time import sleep
from typing import List

from icrawler.builtin import BingImageCrawler
from selenium.webdriver.remote.errorhandler import (NoSuchElementException,
                                                    TimeoutException)


def download_file(url: str, download_file_path: Path) -> int:
    try:
        with urllib.request.urlopen(url) as web_file, open(download_file_path, 'wb') as local_file:
            local_file.write(web_file.read())
    except urllib.error.URLError:
        traceback.print_exc()


def download_files(image_urls: List[str], download_dir_path: Path) -> int:
    for image_url in image_urls:
        download_file(
            image_url,
            download_dir_path / image_url.split('/')[-1]
        )


class ImageCrawler(object):
    def __init__(self, output_dir_path: Path) -> List[str]:
        self.output_dir = output_dir_path
        self.crawler = BingImageCrawler(storage={"root_dir": output_dir_path})

    def run(self, keyword: str, max_num: int) -> List[str]:
        filters = dict(
            size="large",
            type="photo",
            layout="square")

        self.crawler.crawl(keyword=keyword, filters=filters, max_num=max_num)

        return self.get_results()

    def get_results(self) -> List[str]:
        return os.listdir(self.output_dir)


class MySelenium:
    def __init__(self, driver) -> None:
        self.driver = driver

    def click(self, element):
        self.driver.execute_script('arguments[0].click();', element)

    def get_top_image_url(self) -> str:
        url = self.driver \
            .find_element_by_class_name('hero__img-container') \
            .find_element_by_tag_name('img') \
            .get_attribute('src')
        return url

    def load_more(self, button_name) -> None:
        while True:
            elements = self.driver.find_elements_by_xpath('//div/button')
            elements = [e for e in elements if e.text == button_name]
            if len(elements) == 0:
                break
            else:
                for e in elements:
                    self.click(e)
                    sleep(3)

    def crawle_gallary(self, e) -> List[str]:
        self.click(e)
        url_list = list(set(
                e.find_element_by_tag_name('img').get_attribute('src') + '.jpg'
                for e in self.driver.find_elements_by_class_name('release-gallery__img-container')
        ))
        self.click(self.driver.find_element_by_class_name('release-gallery__close'))
        return url_list

    def crawle_release_page(self, url) -> List[str]:
        self.driver.get(url)
        sleep(1)
        url_list = []
        url_list.append(self.get_top_image_url())
        try:
            first_element = self.driver \
                .find_element_by_id('page-content') \
                .find_element_by_class_name('release-thumb__img-container')
            url_list.extend(self.crawle_gallary(first_element))
        except NoSuchElementException:
            pass
        return url_list

    def crawle_model_page(self, url):
        self.driver.get(url)
        sleep(1)
        url_list = []
        top_image_url = self.get_top_image_url()
        url_list.append(top_image_url)
        self.load_more('VIEW MORE RELEASES')
        elements = self.driver.find_elements_by_class_name('sd-node__preview-item')
        releases_url = [e.find_element_by_tag_name('a').get_attribute('href') for e in elements]
        print(f'Found {len(releases_url)} releases')
        for url in releases_url:
            try:
                url_list += (self.crawle_release_page(url))
            except TimeoutException:
                print(f'TimeoutException in crawle_release_page: {url}')
            except Exception:
                print(f'Exception in crawle_release_page: {url}')
                traceback.print_exc()
        return url_list

    def crawle_line_page(self, url):
        self.driver.get(url)
        sleep(1)
        url_list = []
        self.load_more('VIEW MORE MODELS')
        elements = self.driver.find_elements_by_class_name('sd-node__preview-item')
        model_url = [e.find_element_by_tag_name('a').get_attribute('href') for e in elements]
        print(f'Found {len(model_url)} models')
        for url in model_url:
            try:
                url_list += self.crawle_model_page(url)
            except TimeoutException:
                print(f'TimeoutException in crawle_model_page: {url}')
            except Exception:
                print(f'Exception in crawle_model_page: {url}')
                traceback.print_exc()
        return url_list

    def crawle_brand_page(self, url, exclude_url) -> List[str]:
        self.driver.get(url)
        url_list = []
        self.load_more('VIEW MORE LINES')
        elements = self.driver.find_elements_by_class_name('sd-node__preview-item')
        line_url = [e.find_element_by_tag_name('a').get_attribute('href') for e in elements]
        print(f'Found {len(line_url)} lines')
        for url in line_url:
            if url in exclude_url:
                continue
            url_list += self.crawle_line_page(url)
        return url_list
