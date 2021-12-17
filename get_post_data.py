from crawling.models.instagram import Instagram

if __name__ == "__main__":

    crawler = Instagram()

    info = crawler.get_post_data(post_index=1, post_href='/p/CXixCI9Ll0E/')

    print(info)

    crawler.driver.close()