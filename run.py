import os
from collections import deque

import pandas as pd
import numpy as np

from crawling.models.instagram import Instagram


if __name__ == "__main__":

    # load influencer data

    df = pd.read_csv("data/influencer_dataframe.csv", sep=';', index_col=0)

    # initiate webbot for access influencer's front page

    saved_folder = 'data/influencer'

    connector_front = Instagram()
    connector_post = Instagram()

    for instagram_id in df['instagram_id'].values:

        if os.path.isfile(f"{saved_folder}/{instagram_id}.csv"):
            continue

        connector_front.access_influencer_account(instagram_id)
        info = {}
        info.update(connector_front.account_verification())
        metadata = connector_front.get_metadata()
        if not metadata:
            continue
        else:
            info.update(metadata)

        article_section_html = connector_front.get_article_section()

        article_section_rows_html = article_section_html.find_all('div', {'class': 'Nnq7C weEfm'})

        like_list = []
        comment_list = []

        # 資料結構 FAANG 技術考試必考題。
        queue = deque()

        # 抓取目前所有href
        for row in article_section_rows_html:
            all_post_front_html = row.find_all('div', {'class': 'v1Nh3'})
            for post_front_html in all_post_front_html:
                href = post_front_html.find('a').get('href')
                queue.append(href)

        n_of_articles = 0
        while (n_of_articles < 10) and queue:
            href = queue.popleft()
            info.update(connector_post.get_post_data(post_index=n_of_articles, post_href=href))
            info.update(connector_front.number_of_comments(post_index=n_of_articles, href=href))

            comment_list.append(info[f'number_of_comments_{n_of_articles}'])
            like_list.append(info[f'number_of_likes_{n_of_articles}'])

            n_of_articles += 1

        info.update({'average_likes': np.mean(like_list),
                     'average_comments': np.mean(comment_list)})
        influencer_df = pd.DataFrame.from_dict({f'{instagram_id}': info})
        influencer_df.to_csv(f"{saved_folder}/{instagram_id}.csv", sep=';')
