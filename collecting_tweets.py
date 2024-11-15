from playwright.sync_api import sync_playwright
from scrape_twitter import get_auth_twitter_pg
from scrape_twitter import get_search_tweets
from util import write_tweets_to_jsonl_file
import os
import gzip
import glob
import json


"""
Scrapes and saves tweets for a given list of keywords.
"""
def tweet_count(input_file):
    """
    Returns the current number of tweets stored in a given scraped tweets file.
    """
    with gzip.open(os.path.join("scraped_tweets",input_file), "r") as f:        
        line_count = sum(1 for line in f)
        return line_count

def get_next_file_number(jsonl_tweets_folder):
    """
    Takes in the directory of existing tweet files containing pre-existing tweet files and returns the file number 
    of the next tweet file to be saved.

    Argument(s): 
    - jsonl_tweets_folder: Directory of existing tweet files.

    Output:
    Integer representing the file number for the newest tweet file.
    """
    if not os.path.exists(jsonl_tweets_folder):
        return 1
    base_name = 'scraped_tweets'
    extension = '.json.gz'
    # Get all the files in the folder that start with the base_name and end with the extension
    existing_files = [f for f in os.listdir(jsonl_tweets_folder) if f.startswith(base_name) and f.endswith(extension)]
    if existing_files == []:
        return 1
    # Extract numbers from the file names (assuming the pattern is base_nameX.extension)
    file_numbers = [int(f[len(base_name):-len(extension)]) for f in existing_files if f[len(base_name):-len(extension)].isdigit()]
    # Determine the next file number
    next_file_number = max(file_numbers, default=0) + 1
    return next_file_number

def combine_files(jsonl_tweets_folder, combined_filename, new=True):
    """
    Takes in the directory of existing tweet files and the final file name for newest file. Combines SERP files into 
    one file and stores it in the directory of existing tweet files with the proper file name for the current 
    iteration of main().

    Argument(s): 
    - jsonl_tweets_folder: Directory of existing tweet files.
    - combined_filename: String representing file name for final file.
    - new: If True, writes a new combined file. If False, appends to an already existing file.

    Output:
    Adds the newest file to the directory of existing tweet files with the proper file name for the current 
    iteration of main().
    """
    if new:
        mode_arg = 'wt'
    else:
        mode_arg = 'at'
    # Fetch all .jsonl.gz tweet files 
    input_files = glob.glob(os.path.join(jsonl_tweets_folder, 'twitter_serp*.json.gz'))
    # Write new combined file or append to an existing file
    with gzip.open(os.path.join(jsonl_tweets_folder, combined_filename), mode_arg) as outfile:
        # Iterate through each file
        for file in input_files:
            # Read and write each tweet into combined file
            with gzip.open(file, 'rt') as infile:
                for line in infile:
                    outfile.write(line)
            # Remove file once processed
            os.remove(file)


def scrape_tweets(jsonl_tweets_folder, keywords, max_tweets, total_tweets_to_scrape):
    """
    The function will scrape a subset of tweets for each keyword and saves those to a temporary json gzip file. 

    Argument(s):
    - jsonl_tweets_folder: Directory of scraped tweet files.
    - keywords: List of strings representing keywords to be scraped
    - max_tweets: Integer representing the maximum number of tweets to be collected 
    during one iteration of get_search_tweets()
    - total_tweets_to_scrape: Integer representing the total number of tweets to collect after one iteration
    of main()

    Output:
    Adds one SERP json gzip file to the tweet file directory for each keyword. 
    """
    # Open twitter and prompt login
    playwright = sync_playwright().start()
    browser_dets = get_auth_twitter_pg(playwright)
    # Divide tweets for each topic
    tweets_per_topic = total_tweets_to_scrape//len(keywords)
    iter_per_topic = tweets_per_topic//max_tweets    
    # Create a storage folder if one does not exist
    if not os.path.exists(jsonl_tweets_folder):
        os.makedirs(jsonl_tweets_folder)
    # Iterate through topics and extract tweets
    for i, topic in enumerate(keywords):
        if tweets_per_topic <= max_tweets:
            tweets = get_search_tweets(browser_dets, topic, max_tweets=tweets_per_topic)
            # Name and store data in json file 
            jsonl_data_path = os.path.join(jsonl_tweets_folder, 'twitter_serp' + str(i+1) + '_1.json.gz')    
            write_tweets_to_jsonl_file(jsonl_data_path, tweets['tweets'])
        else:
            for j in range(iter_per_topic):
                tweets = get_search_tweets(browser_dets, topic, max_tweets=max_tweets) 
                # Name and store data in json file 
                jsonl_data_path = os.path.join(jsonl_tweets_folder, 'twitter_serp' + str(i+1) + '_' + str(j+1) + '.json.gz')    
                write_tweets_to_jsonl_file(jsonl_data_path, tweets['tweets'])
    
    playwright.stop()


def main(keywords, max_tweets=100, total_tweets_to_scrape=500):
    """
    The function will scrape a subset of tweets for each keyword and saves those to a temporary json gzip file. 
    After we have one SERP file for each keyword, the files are combined into one and saved in the directory of 
    existing tweet files with the proper file name.

    Argument(s):
    - keywords: List of strings representing keywords to be scraped
    - max_tweets: Integer representing the maximum number of tweets to be collected 
    during one iteration of get_search_tweets()
    - total_tweets_to_scrape: Integer representing the total number of tweets to collect after one iteration
    of main()

    Output:
    Adds one json gzip file to the directory of existing tweet files. This file holds all tweets scraped for one 
    iteration of tweet collection. 
    """
    # Initialize a directory to store scraped tweets
    jsonl_tweets_folder = "scraped_tweets"
    # Collect tweets
    scrape_tweets(jsonl_tweets_folder, keywords, max_tweets, total_tweets_to_scrape)

    # Fetch the next file number to prevent overwriting files
    next_file_number = get_next_file_number(jsonl_tweets_folder)

    # Join all json.gz files
    combine_files(jsonl_tweets_folder, f'scraped_tweets{next_file_number}.json.gz')

    # Check if the expected number of tweets were collected in the file. If not, collect more tweets.
    current_scraped_count = tweet_count(f'scraped_tweets{next_file_number}.json.gz')
    while current_scraped_count < total_tweets_to_scrape:
        # Scrape more tweets
        scrape_tweets(jsonl_tweets_folder, keywords, 10, 50)
        combine_files(jsonl_tweets_folder, f'scraped_tweets{next_file_number}.json.gz', new=False)
        # Recount number of scraped tweets
        current_scraped_count = tweet_count(f'scraped_tweets{next_file_number}.json.gz')

if __name__ == "__main__":
    # keywords = list(input("What keywords would you like to use for tweet collection? (Ex. a, b, c, d, e): \n").split(', '))
    # Social justice, Climate Change, #MeToo, #BlackLivesMatter, US Immigrant Rights
    keywords = list('Social justice, Climate Change, #MeToo, #BlackLivesMatter, US Immigrant Rights'.split(', '))
    main(keywords, max_tweets=100, total_tweets_to_scrape=200)