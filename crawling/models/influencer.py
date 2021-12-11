from typing import Dict, List

import bs4
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from crawling.models.connector import Connector


class Influencer:

    """ A class for influencer crawling on starngage.

    Attributes:
        main_url: a url to starngage.
        wait: An object for implicit waiting until the appearance of certain element.
        driver: google chrome web interacting object

    Methods:

    """

    def __init__(self, turn_off_image: bool = False, package: str = 'seleniumwire'):
        self.connector = Connector(package=package, turn_off_image=turn_off_image)
        self.main_url = "https://starngage.com/app/us/influencer/ranking"

        self.driver = self.connector.driver
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get(self.main_url)
        self.plp_html = None

    def get_top_n_influencers(self, n: int) -> List:

        all_influencer = []

        while len(all_influencer) < n:

            self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[2]/div/div/table')))

            plp_html = self.connector.get_bs4_page_html()

            table_html = plp_html.find('table', {'class': 'table table-hover table-responsive-sm'})

            rows_html = table_html.find('tbody').find_all('tr')

            for row_html in rows_html:
                all_influencer.append(self.exact_influencer_info(row_html))

            # after finishing crawler the current page, we move to the next page:
            icons_html = plp_html.find('ul', {'class': 'pagination justify-content-center'}).find_all('li')
            next_page_html = icons_html[-1]
            next_page_url = next_page_html.find('a').get('href')

            self.driver.get(next_page_url)

        assert len(all_influencer) == n, 'number does not match'

        return all_influencer

    def exact_influencer_info(self, row_html: bs4.element.Tag) -> Dict:

        influencer_content = row_html.find('td', {'class': 'align-middle text-break'}).contents
        influencer_name = influencer_content[0]
        instagram_id = influencer_content[-1].text
        topics_html = row_html.find_all('span', {'class': 'badge badge-pill badge-light samll text-muted'})
        topics = ' '.join([topic_html.find('a').text for topic_html in topics_html])
        # the last two are the number of followers and engagement rate
        followers = row_html.find_all('td')[-2].text
        engagement_rate = row_html.find_all('td')[-1].text

        # You can transform followers and engagement_rate from str to int and float, respectively, if you need.

        influencer_dict = {'name': influencer_name,
                           'instagram_id': instagram_id,
                           'topics': topics,
                           'followers_starngage': followers,
                           'engagement_rate_starngage': engagement_rate}

        return influencer_dict


if __name__ == "__main__":

    crawler = Influencer()

    list_of_influencer = crawler.get_top_n_influencers(1000)

    crawler.driver.close()