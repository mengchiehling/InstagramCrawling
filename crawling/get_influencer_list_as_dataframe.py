import os

import pandas as pd

from crawling.models.influencer import Influencer
from crawling.io.path_definition import get_project_dir

if __name__ == "__main__":

    crawler = Influencer()

    list_of_influencer = crawler.get_top_n_influencers(1000)

    df_influencer = pd.DataFrame(list_of_influencer)

    dir_result = f"{get_project_dir()}/data"

    if not os.path.isdir(dir_result):
        os.makedirs(dir_result)

    df_influencer.to_csv(f"{dir_result}/influencer_dataframe.csv", sep=";")

    crawler.driver.close()