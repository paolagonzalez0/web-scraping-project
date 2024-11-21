import gzip
import json

def proc_tweet(tweet_data):
    """
    Processes a tweet's data and prints information about the tweet such as author, timestamp, text, 
    and links if they exist, as well as indicating if the tweet is a retweet.

    Parameters:
        tweet_data (dict): A dictionary containing tweet data including user information, tweet content, 
        and tweet metadata such as retweet status.

    Returns:
        None
    """
    
    # Check if the tweet is a retweet and print retweet information
    if tweet_data['notes']['is_retweet'] is True:
        print('Retweeted by:', tweet_data['notes']['timeline_screen_name'])

    # Gather information about the tweet
    screen_name = tweet_data['user']['screen_name']  # The username of the tweet's author
    created_at = tweet_data['created_at']            # Timestamp when the tweet was created
    verified = tweet_data['user']['verified']        # Whether the tweet's author is verified
    text = tweet_data['text']                        # Text content of the tweet
    uid = tweet_data['id_str']                       # Unique tweet ID

    # Collect links found in the tweet's text, if any
    links = []
    if 'urls' in tweet_data.get('entities', []):
        for link in tweet_data['entities']['urls']:
            links.append(link['expanded_url'])  # Append expanded URL to the links list
    
    # Print out the tweet's information
    print(uid + "\t" + created_at + "\t" + screen_name)  # Print tweet ID, creation time, and author's username
    for link in links:  # Print each link found in the tweet
        print("  " + link)
    print()  # Add a newline for readability after each tweet's output


# Open the gzipped file containing the tweet data
with gzip.open('acnwala_timeline.json.gz', 'rb') as infile:
    # Counter for reading tweet data and processing it
    counter = 1
    for tweet in infile:  # Iterate over each tweet in the gzipped file
        tweet = json.loads(tweet.decode())  # Decode the tweet from bytes and load as a JSON object
        
        # Print progress by displaying which tweet number is being read
        print(f'reading tweets: {counter}')
        
        # Process and print information about the tweet
        proc_tweet(tweet)
        
        print()  # Print an empty line between tweets for readability
        counter += 1  # Increment the counter to track the number of tweets processed
