from scripts.collecting_tweets import get_topics, collect_tweets
from scripts.extracting_links import extract_links, link_count
from scripts.get_timemaps import save_timemaps
import math
import shutil

def main():
    '''
    Runs the main program excluding the memento analysis. Scrapes tweets via web scraping, extracts requested number of URIs, and collects 
    timemap for each URI.
    '''
    # Will be taken in from the command line
    total_links_to_scrape = 150

    # Scrape 200 tweets to start on 5 random social movements
    keywords = get_topics(5)
    collect_tweets(keywords, total_tweets_to_scrape=200)
    # Extract links in those tweets
    result = extract_links(total_links_to_scrape=total_links_to_scrape)
    # If not enough links were collected, scrape more tweets and extract more links.
    while result is not None:
        # Get the number of links still needed and collect double the amount of tweets
        tweets_to_scrape = int((total_links_to_scrape - link_count()) * 2)
        # Round to be a multiple of 5 for easier processing
        tweets_to_scrape = math.ceil(tweets_to_scrape / 5) * 5
        print(f'Collecting {tweets_to_scrape} more tweets..')
        # Get new topics to avoid rate-limiting
        keywords = get_topics(5)
        collect_tweets(keywords, total_tweets_to_scrape=tweets_to_scrape)
        result = extract_links(total_links_to_scrape=total_links_to_scrape, file_number=result)
    # Fetch the time map for each URI
    save_timemaps()

    # After tweet collection, delete cache and browser storage
    shutil.rmtree("__pycache__")
    shutil.rmtree("playwright-browser-storage")

    return


if __name__ == "__main__":
    main()