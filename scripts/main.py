from collecting_tweets import get_topics, collect_tweets
from extracting_links import extract_links, link_count
from get_timemaps import save_timemaps
import math
import shutil
import argparse

def main():
    '''
    Runs the main program excluding the memento analysis. Scrapes tweets via web scraping, extracts requested number of URIs, and collects 
    timemap for each URI.
    '''
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the tweet scraping and link processing pipeline.")
    parser.add_argument(
        "--total_links_to_scrape", 
        type=int, 
        default=50, 
        help="Total number of links to scrape (default: 50)"
    )
    # Fetch the number of links to scrape
    args = parser.parse_args()
    total_links_to_scrape = args.total_links_to_scrape

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

    # After tweet collection, delete cache and browser storage
    shutil.rmtree("__pycache__")
    shutil.rmtree("playwright-browser-storage")

    # Fetch the time map for each URI
    save_timemaps()

    return

if __name__ == "__main__":
    main()