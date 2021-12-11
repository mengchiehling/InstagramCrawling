import random
import time

import bs4
from user_agent import generate_user_agent
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, NoSuchWindowException
from bs4 import BeautifulSoup

from crawling.settings import MAX_SLEEP, MAX_RETRY, IS_STOPPED_AFTER_MAX_RETRY


class Connector:

    """Class Connector can be considered as the crawling engine instance initialization.
    Attributes:
        driver: the interactive web crawling engine. Can be either from package Selenium or SeleniumWire

    Methods:
        get_product_content_page_from_url: Entrance point of parsing an html page source code by BeautifulSoup into an html DOM
        get_bs4_page_content_tags: Parse the webpage currently visited by driver into an HTML DOM by BeautifulSoup
    """

    def __init__(self, headless: bool = False, package: str = "selenium", turn_off_image: bool = False):

        """
        Args:
            headless: if runs Chrome in headless mode.
            turn_off_image: if turn off showing images
            package: specify from which package the interactive engine is called.
        """

        self.__headless = headless
        self.__package = package
        self.__chrome_initialization(turn_off_image=turn_off_image)
        self.__retry = 0

    def __get_response(self) -> bs4.element.Tag:

        """
        Returns:
            Raw html source code

        Raises:
            RuntimeError:
                TimeoutException: if the element specified in wait_condition cannot be found
                Exception: something goes wrong, need further investigation... ToDo
        """

        try:
            self.driver.get(self.__url)
        except TimeoutException as e:
            print(f"Timeout for getting {self.__url}")
            raise RuntimeError(f"{e}")

        if self.__driver_sleep_time is not None:
            time.sleep(self.__driver_sleep_time)

        if self.__wait_condition is not None:
            try:
                WebDriverWait(self.driver, 10).until(self.__wait_condition)
            except (TimeoutException, NoSuchWindowException) as e:
                print(f"Timeout for waiting condition too long")
                raise RuntimeError(f"{e}")

        if self.__complete_state:
            try:
                complete_state = self.driver.execute_script('return document.readyState;')
                while complete_state != 'complete':
                    time.sleep(3)
                    complete_state = self.driver.execute_script('return document.readyState;')
            except UnexpectedAlertPresentException as e:
                raise RuntimeError(f"{e}")

        if self.__scroll_to_buttom:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        return self.driver.page_source

    def get_plp_from_url(self, url: str, scroll_to_buttom: bool = True,
                         driver_sleep_time: int = None, random_sleep_time: bool = True,
                         wait_condition=None, complete_state: bool = True) -> bs4.element.Tag:

        """
        Entrance point of parsing an html page source code by BeautifulSoup into an html DOM

        Args:
            url: url to the product page
            scroll_to_buttom: if scroll the page to the button such that all the components become visible
            driver_sleep_time: finite sleep time so self.driver can load the information
            random_sleep_time: random sleep time to prevent Bot check
            wait_condition: driver waits until something in the page is there
            complete_state: if the engine driver should wait until document.readyState

        Returns:
            html DOM parsed by BeautifulSoup

        Raises:
            RuntimeError: It the webpage cannot be properly loaded for MAX_RETRY times

        """

        self.__url = url
        self.__scroll_to_buttom = scroll_to_buttom
        self.__driver_sleep_time = driver_sleep_time
        self.__wait_condition = wait_condition
        self.__complete_state = complete_state

        while True:  #
            try:
                if random_sleep_time:
                    random_sleep = random.randint(1, MAX_SLEEP)
                    time.sleep(random_sleep)  # turn off at the moment

                self.__get_response()

                plp_html = self.get_bs4_page_html()
                self.__retry = 0
                return plp_html
            except IndexError:
                pass
            except RuntimeError as ex:
                # See if this is an Amazon page without product, if yes then skip
                plp_html = self.get_bs4_page_html()
                self.__retry += 1
                print(f'Attempt #{self.__retry}. Exception: {ex} - url: {url}')
                if self.__retry <= MAX_RETRY:
                    plp_html = self.get_plp_from_url(self.__url, scroll_to_buttom=scroll_to_buttom,
                                                     random_sleep_time=random_sleep_time,
                                                     wait_condition=wait_condition)
                    return plp_html
                else:
                    if IS_STOPPED_AFTER_MAX_RETRY:
                        self.__retry = 0
                        raise RuntimeError(f"Unable to get {self.__url.split('/')[-1]} properly")

    def __chrome_initialization(self, turn_off_image: bool):

        """
        Launch the interactive web crawling engine

        Args:
            turn_off_image: if turn off showing images
        """

        assert self.__package in ['selenium', 'seleniumwire'], "wrong web bot package"

        if self.__package == 'selenium':
            from selenium import webdriver
        else:
            from seleniumwire import webdriver

        chrome_options = webdriver.ChromeOptions()
        if self.__headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=1920,1080")

        # User a randomly generated user agent
        user_agent = generate_user_agent(os='mac', navigator='chrome')  # USER_AGENT

        chrome_options.add_argument(f"--user-agent=%s" % user_agent)
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])

        # disable image and javascript loading
        if turn_off_image:
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,
                    'javascript': 2
                }
            }
            chrome_options.add_experimental_option('prefs', prefs)

        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chrome_options)
        self.driver.set_page_load_timeout(60)  # set page load timeout to 60 seconds

    def get_bs4_page_html(self) -> bs4.element.Tag:

        """
        parsing html DOM with BeautifulSoup

        Returns:
            DOM derived from web page source code parsed by BeautifulSoup
        """

        return BeautifulSoup(self.driver.page_source, "html.parser")
