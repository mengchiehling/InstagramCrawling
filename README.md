# InstagramCrawling

1. Setup virtual environment:

    `bash setup_conda_environment.sh`

2. Collecting top 1000 influencers from https://starngage.com/app/us/influencer/ranking: 
    
    `python -m crawling.get_influencer_list_as_dataframe`
    
3. Execution crawling process:
    
    `python -m crawling.run`