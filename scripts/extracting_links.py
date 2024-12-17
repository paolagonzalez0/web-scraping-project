import gzip
import json
import glob
import os
import requests
import numpy as np
import re
import collecting_tweets

"""
This script extracts unique links from tweets stored in the scraped_tweets directory and stores them in a text file. 
Additionally, it resolves each URI to its final target URI and filters out links pointing to a twitter or 
video/audio-only page. 
"""

def check_link_validity(link):
    """
    Checks if a given URI is valid (i.e. does not point to a twitter or video/audio-only page). Returns True if the 
    link is valid, returns False if the link is not valid.

    Argument(s):
    - link: String representing URI.

    Output:
    Boolean value representing link validity.
    """
    invalid_links = ['twitter.com',  
                     'youtube.com', 
                     'twitch.com',
                     'twitch.tv',
                     'soundcloud.com',
                     '/x.com',
                     'tiktok.com'
                     ]
    for invalid_link in invalid_links:
        if invalid_link in link:
            return False
    return True

def extract_links_subset(file_number=1):
    """
    Extracts the links of the corresponding file.
    
    Argument(s):
    - file_number: Integer representing the file where URI extraction will occur.

    Output:
    Returns a numpy array of all unique URIs extracted. 
    """
    tweet_counter = 1
    links = []
    st_files = glob.glob(os.path.join('../scraped_tweets', 'scraped_tweets*.json.gz'))
    # Sort the files by extracting the file number
    st_files = sorted(st_files, key=lambda x: int(re.search(r'\d+', x).group()))
    with gzip.open(st_files[file_number-1], 'rb') as infile:
        for tweet in infile:
            # print('Reading tweet',tweet_counter,'..')
            tweet_counter += 1
            try:
                tweet = json.loads(tweet.decode())
                tweet_urls = tweet['entities']['urls']
                if tweet_urls == []:
                    continue
                else:
                    # Fetch the final URI (returns HTTP 200 response)
                    response = requests.get(tweet_urls[0]['expanded_url'], timeout=5)
                    if response.status_code == 200:
                        final_link = response.url
                    # Exclude link if it points to a video/audio-only page
                    if check_link_validity(final_link):
                        links.append(final_link)
                    # Exclude link if it does not return 200 response
                    else:
                        continue
            except:
                continue

    print("Processed", tweet_counter-1, "tweets..")
    print("Collected", len(np.unique(links)), "links..")
    return np.unique(links)

def link_count():
    """
    Counts the current number of links stored in the tweet_links.txt file.

    Output:
    Integer representing the number of URIs stored in tweet_links.txt
    """
    if not os.path.exists('../tweet_links.txt'):
        return 0
    else:
        with open('../tweet_links.txt', 'r') as file:
            line_count = sum(1 for line in file)
        return line_count
    
def read_duplicates():
    """
    Creates a list of existing duplicate URIs in the tweet_links.txt file.

    Output:
    Returns a list of duplicate URI strings in tweet_links.txt.
    """
    with open('../tweet_links.txt', 'r') as file:
        existing_links = file.read().splitlines()
        read_links = []
        duplicate_links = []
        for link in existing_links:
            if link in read_links:
                duplicate_links.append(link)
            else:
                read_links.append(link)

        return duplicate_links
    
def extract_links(total_links_to_scrape=50,file_number=1):
    """
    Takes in the total number of links to extract and a file number at which to start URI extraction. 
    Creates a final file tweet_links.txt containing the 1000 unique links.

    Argument(s):
    - total_links_to_scrape: Integer representing the total number of URIs to extract and save.
    - file_number: Integer representing the file at which to start URI extraction.

    Output:
    Executes the URI extraction process, updating the tweet_links.txt file with the extracted URIs. 
    Returns the file number of the last processed file, or None if all links have been collected.
    """
    current_file = file_number
    while link_count() < total_links_to_scrape:
        # Do not collect URIs from files that do not exist
        if current_file >= collecting_tweets.get_next_file_number('../scraped_tweets'):
            return current_file
        # Extract link from tweets
        print(f"Extracting URIs from file {current_file}..")
        extracted_links = extract_links_subset(current_file) 
        link_file_path = "../tweet_links.txt"
        # Create link txt file
        if not os.path.exists(link_file_path):
            with open(link_file_path, 'w') as file:
                for link in extracted_links:
                    file.write(link + '\n')
        else:
            # Fetch existing links in txt file
            try:
                with open(link_file_path, 'r') as file:
                    existing_links = file.read().splitlines()
            except:
                existing_links = []
            # Add link to the txt file if not in the file
            with open(link_file_path, 'a') as file:
                for link in extracted_links:
                    if link not in existing_links: file.write(link + '\n')
        print(f"Finished extracting links from files..")
        print(f'Link count: ', link_count())
        current_file += 1
    return None
    
if __name__ == "__main__":
    # result = extract_links(total_links_to_scrape=150)
    pass