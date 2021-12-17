from crawling.models.instagram import Instagram

if __name__ == "__main__":

    crawler = Instagram()

    info = {}

    crawler.access_influencer_account('@therock')

    info.update(crawler.account_verification())
    info.update(crawler.get_metadata())

    print(info)

    crawler.driver.close()