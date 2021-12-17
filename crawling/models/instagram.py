import time
from time import perf_counter
from typing import Dict
from datetime import datetime

import bs4
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from crawling.models.connector import Connector
from crawling.settings import INSTAGRAM


class Instagram:

    """ A class for Instagram crawling.

    Attributes:
        main_url: a url to Instagram login page.
        wait: An object for implicit waiting until the appearance of certain element.
        driver: google chrome web interacting object

    Methods:

    """

    def __init__(self, turn_off_image: bool = False):
        self.connector = Connector(turn_off_image=turn_off_image)
        self.main_url = "https://www.instagram.com/accounts/login/"

        self.driver = self.connector.driver
        self.wait = WebDriverWait(self.driver, 10)
        self.plp_html = None

        # access the login page:

        self.driver.get(self.main_url)
        self.click_cookie()
        self.login()

    def click_cookie(self):

        '''
        Click the cookie
        '''

        while True:
            try:
                click_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div/button[1]')))
                break
            except TimeoutException:
                time.sleep(1)
        click_button.click()

    def login(self):

        '''
        Automatic account login
        '''

        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "KPnG0")))  # util login page appear
        time.sleep(3)

        user = self.wait.until(EC.element_to_be_clickable((By.NAME, "username")))   # self.driver.find_element_by_name("username")
        user.click()
        time.sleep(3)
        user.send_keys(INSTAGRAM['username'])

        passwd = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))  # self.driver.find_element_by_name('password')
        passwd.click()
        time.sleep(3)
        passwd.send_keys(INSTAGRAM['password'])

        login_button_ = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        login_button_.click()
        time.sleep(10)

    def access_influencer_account(self, instagram_id: str):

        url = instagram_id.replace("@", "https://www.instagram.com/")

        self.driver.get(url)

    def account_verification(self) -> Dict:

        '''
        查看藍勾勾認證
        '''

        time_start = perf_counter()

        verified = 0

        while True:
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//span[@title="Verified"]')))
                verified = 1
                break
            except TimeoutException:
                print("Unable to find the verified symbol yet")
                time_end = perf_counter()
                if (time_end - time_start) > 30:
                    print("Unable to find the verified symbol.")
                    break

        return {'verified': verified}

    def get_metadata(self) -> Dict:

        '''

        Returns:
            a tuple of number of posts, number of followers, and number of follows
        '''
        while True:
            try:
                self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'k9GMp')))
                break
            except TimeoutException:
                print("Unable to find the metadata yet")

        self.instagram_page_html = self.connector.get_bs4_page_html()
        influencer_metadata = self.instagram_page_html.find_all('li', {'class': 'Y8-fY'})

        number_of_post = influencer_metadata[0].find('span', {'class': 'g47SY'}).text
        number_of_follower = influencer_metadata[1].find('span', {'class': 'g47SY'}).text
        number_of_follows = influencer_metadata[2].find('span', {'class': 'g47SY'}).text

        return {'number_of_post': number_of_post, 'number_of_follower': number_of_follower,
                'number_of_follows': number_of_follows}

    def get_article_section(self) -> bs4.element.Tag:

        article_section_html = self.instagram_page_html.find('main').find('article')

        return article_section_html

    def get_post_data(self, post_index: int, post_href: str):

        time_start = perf_counter()

        self.driver.get(f"https://www.instagram.com{post_href}")

        while True:
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, '//article[@role="presentation"]')))
                break
            except TimeoutException:
                print("Unable to find the post yet")
                time_end = perf_counter()
                if (time_end - time_start) > 30:
                    print("Unable to find the post.")
                    break

        post_html = self.connector.get_bs4_page_html()

        # like
        number_of_likes = post_html.find('a', {'class': 'zV_Nj'}).find('span').text

        # comments: skip because another method is required.

        # time
        time = post_html.find('time', {'class': '_1o9PC Nzb55'}).get('datetime')
        time = datetime.strptime(time[:-5], "%Y-%m-%dT%H:%M:%S")
        weekday = time.weekday()

        # video or image
        is_video = self.is_video_check()

        return {'number_of_likes': number_of_likes, 'post_time_weekday': weekday,
                'is_video': is_video}

    def is_video_check(self) -> int:

        time_start = perf_counter()

        is_video = 0

        while True:
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, '//video[@class="tWeCl"]')))
                print("This is a video post")
                is_video = 1
                break
            except TimeoutException:
                print("Unable to find the video tag yet")
                time_end = perf_counter()

                # try if it is an image:
                try:
                    self.wait.until(EC.presence_of_element_located((By.XPATH, '//img[@class="FFVAD"]')))
                    print("This is an image post")
                    break
                except TimeoutException:
                    pass

                if (time_end - time_start) > 30:
                    print("Unable to find the video tag symbol.")
                    break

        return is_video

    def if_tracking_others(self):

        pass

    def number_of_comments(self, href):

        post_elem = self.driver.find_element_by_xpath('//a[@href="' + str(href) + '"]')
        action = ActionChains(self.driver)

        action.move_to_element(post_elem).perform()

        n_like_elem = self.driver.find_elements_by_class_name('-V_eO')

        number_of_comments = n_like_elem[1].text

        return {'number_of_comments': number_of_comments}
