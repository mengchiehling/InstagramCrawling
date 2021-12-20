import time
import re
from time import perf_counter
from typing import Dict, Optional
from datetime import datetime

import bs4
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

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
        self.number_extractor_regex = re.compile('[\d.]+')

        # access the login page:

        self.driver.get(self.main_url)
        self.click_cookie()

        while True:
            self.login()
            time.sleep(3)
            try:
                self.driver.find_element_by_xpath('//p[@id="slfErrorAlert"]')
                self.driver.refresh()
                time.sleep(10)
            except NoSuchElementException:
                break

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

        while True:
            try:
                user = self.wait.until(EC.element_to_be_clickable((By.NAME, "username")))
                user.click()
                break
            except (TimeoutException,  ElementClickInterceptedException) as e:
                print(e)

        time.sleep(3)
        user.send_keys(INSTAGRAM['username'])

        while True:
            try:
                passwd = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
                break
            except TimeoutException:
                pass

        passwd.click()
        time.sleep(3)
        passwd.send_keys(INSTAGRAM['password'])

        login_button_ = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        login_button_.click()

    def access_influencer_account(self, instagram_id: str):

        url = instagram_id.replace("@", "https://www.instagram.com/")

        while True:
            try:
                self.driver.get(url)
                break
            except TimeoutException:
                print(f"Keep accessing {url}")

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
                if (time_end - time_start) > 10:
                    print("Unable to find the verified symbol.")
                    break

        return {'verified': verified}

    def get_metadata(self) -> Optional[Dict]:

        '''

        Returns:
            a tuple of number of posts, number of followers, and number of follows
        '''

        time_start = perf_counter()
        while True:
            try:
                self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'k9GMp')))
                break
            except TimeoutException:
                print("Unable to find the metadata yet")
                time_end = perf_counter()
                if (time_end - time_start) > 10:
                    print("Unable to find the metadata")
                    return None

        self.instagram_page_html = self.connector.get_bs4_page_html()
        influencer_metadata = self.instagram_page_html.find_all('li', {'class': 'Y8-fY'})

        number_of_post = influencer_metadata[0].find('span', {'class': 'g47SY'}).text
        number_of_follower = influencer_metadata[1].find('span', {'class': 'g47SY'}).text
        number_of_follows = influencer_metadata[2].find('span', {'class': 'g47SY'}).text

        # process number of post:
        number_of_post = int(number_of_post.replace(",", ""))
        # process number of follower:
        number_of_follower = number_of_follower.replace(",", "")
        basic_num = float(self.number_extractor_regex.findall(number_of_follower)[0])

        if 'k' in number_of_follower:
            basic_num = basic_num * 1000
        if 'm' in number_of_follower:
            basic_num = basic_num * 1000000

        number_of_follower = int(basic_num)
        # process number of follows:
        number_of_follows = int(number_of_follows.replace(",", ""))

        return {'number_of_post': number_of_post, 'number_of_follower': number_of_follower,
                'number_of_follows': number_of_follows}

    def get_article_section(self) -> bs4.element.Tag:

        article_section_html = self.instagram_page_html.find('main').find('article')

        return article_section_html

    def get_post_data(self, post_index: int, post_href: str):

        self.connector.patient_page_load(f"https://www.instagram.com{post_href}")

        while True:
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, '//article[@role="presentation"]')))
                break
            except TimeoutException:
                print("Unable to find the post yet")

                self.driver.refresh()

        post_html = self.connector.get_bs4_page_html()

        # like
        # there are two possibility: video or image
        is_video = self.is_video_check()

        try:
            number_of_likes = self.driver.find_element_by_xpath('//a[@class="zV_Nj"]').find_element_by_tag_name('span').text
        except NoSuchElementException:
            print('No number of likes element')
            while True:
                try:
                    button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@class="vcOH2"]')))
                    button.click()
                    ele = self.driver.find_element_by_xpath('//div[@class="vJRqr"]')
                    number_of_likes = ele.find_element_by_tag_name('span').text
                    break
                except TimeoutException:
                    print('button cannot be clicked yet')

        # number_of_likes: str -> int
        try:
            number_of_likes = int(number_of_likes.replace(",", ""))
        except ValueError:
            number_of_likes = 0

        # comments: skip because another method is required.

        # time
        time_string = post_html.find('time', {'class': '_1o9PC Nzb55'}).get('datetime')
        time_string = datetime.strptime(time_string[:-5], "%Y-%m-%dT%H:%M:%S")
        weekday = time_string.weekday()
        hour = time_string.hour

        # if tracking_others:
        if_tracking_others = self.if_tracking_others()

        return {f'number_of_likes_{post_index}': number_of_likes, f'post_time_weekday_{post_index}': weekday,
                f'is_video_{post_index}': is_video, f'post_time_hour_{post_index}': hour,
                f'if_tracking_others_{post_index}': if_tracking_others}

    def is_video_check(self) -> int:

        time_start = perf_counter()

        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//video[@class="tWeCl"]')))
            print("This is a video post")
            return 1
        except TimeoutException:
            pass

        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//img[@class="FFVAD"]')))
            print("This is an image post")
            return 0
        except TimeoutException:
            pass

    def if_tracking_others(self):

        try:
            self.driver.find_element_by_xpath('//a[@class="notranslate"]')
            return 1
        except:
            return 0

    def number_of_comments(self, post_index: int, href: str):

        post_elem = self.driver.find_element_by_xpath('//a[@href="' + str(href) + '"]')
        action = ActionChains(self.driver)

        action.move_to_element(post_elem).perform()

        try:
            n_like_elem = self.driver.find_elements_by_class_name('-V_eO')
            number_of_comments = n_like_elem[1].text.replace(",", "")
        except IndexError:
            print("comments cannot be found")
            return {f'number_of_comments_{post_index}': 0}

        basic_num = float(self.number_extractor_regex.findall(number_of_comments)[0])

        if 'k' in number_of_comments:
            basic_num = basic_num * 1000
        if 'm' in number_of_comments:
            basic_num = basic_num * 1000000

        return {f'number_of_comments_{post_index}': int(basic_num)}
