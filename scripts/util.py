import gzip
import json
import requests
from NwalaTextUtils.textutils import parallelTask
from NwalaTextUtils.textutils import genericErrorInfo

def rehydrate_tweet(twt_id, user_agent='', token='418g769m7fi'):
    """
    Rehydrates a tweet by fetching its metadata using the tweet ID.

    Argument(s):
    - twt_id: String representing the tweet ID.
    - user_agent: Optional string representing the user agent to use for the request. 
      Defaults to a standard Mozilla/Firefox user agent.
    - token: Optional string representing the token required for the request.
      Defaults to a sample token.

    Output:
    Returns a dictionary containing the tweet's metadata if successful, otherwise returns an empty dictionary.
    
    Note:
    To get the token:
    1. Visit 'https://platform.twitter.com/embed/Tweet.html?id=1288498682971795463'
    2. Inspect network traffic in developer tools to find the URI of the GET request which has the token.
    """
    # Initialize request URL and parameters for the tweet data
    url = "https://cdn.syndication.twimg.com/tweet-result"
    querystring = {"id": twt_id, "lang": "en", 'token': token}
    
    # Define headers for the request
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0" if user_agent == '' else user_agent,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://platform.twitter.com",
        "Connection": "keep-alive",
        "Referer": "https://platform.twitter.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        return json.loads(response.text)
    except:
        genericErrorInfo(f"Problem text:\n {response.text}\n")
    
    return {}

def paral_rehydrate_tweets(tweet_ids):
    """
    Rehydrates a list of tweets in parallel using their tweet IDs.

    Argument(s):
    - tweet_ids: List of dictionaries where each dictionary contains:
      - 'tid': Tweet ID.
      - 'notes': Additional information to attach to each tweet's metadata.

    Output:
    Returns a list of dictionaries with rehydrated tweet metadata and attached notes.
    """
    jobs_lst = []
    len_tweet_ids = len(tweet_ids)
    
    # Prepare jobs for parallel execution
    for i in range(len_tweet_ids):
        t = tweet_ids[i]
        keywords = {'twt_id': t['tid'], 'user_agent': ''}
        jobs_lst.append({
            'func': rehydrate_tweet,
            'args': keywords,
            'misc': t['notes'],
            'print': '' if i % 10 else f'\trehydrate_tweet() {i} of {len_tweet_ids}'
        })

    # Execute jobs in parallel
    res_lst = parallelTask(jobs_lst, threadCount=5)
    
    tweets = []
    for r in res_lst:
        r['output']['notes'] = r['misc']
        tweets.append(r['output'])

    return tweets

def writeTextToFile(outfilename, text, extraParams=None):
    """
    Writes text to a specified file.

    Argument(s):
    - outfilename: String representing the file path where text will be saved.
    - text: The text content to write into the file.
    - extraParams: Optional dictionary with additional parameters like verbosity.

    Output:
    Creates a text file with the specified content.
    """
    if extraParams is None:
        extraParams = {}

    extraParams.setdefault('verbose', True)

    try:
        with open(outfilename, 'w') as outfile:
            outfile.write(text)
        
        if extraParams['verbose']:
            print('\twriteTextToFile(), wrote:', outfilename)
    except:
        genericErrorInfo()

def readTextFromFile(infilename):
    """
    Reads text from a specified file.

    Argument(s):
    - infilename: String representing the file path to read from.

    Output:
    Returns the text content of the file as a string.
    """
    text = ''
    try:
        with open(infilename, 'r') as infile:
            text = infile.read()
    except:
        print('\treadTextFromFile() error filename:', infilename)
        genericErrorInfo()
    
    return text

def write_tweets_to_jsonl_file(outfilename, tweets):
    """
    Writes a list of tweets to a compressed JSONL file.

    Argument(s):
    - outfilename: String representing the output file path (.json.gz).
    - tweets: List of dictionaries, each containing tweet data.

    Output:
    Creates a compressed JSONL file with the tweet data.
    """
    try:
        with gzip.open(outfilename, 'wt') as outfile:
            for t in tweets:
                outfile.write(json.dumps(t, ensure_ascii=False) + '\n')
    except:
        genericErrorInfo()

    print(f'\nWrote: {outfilename}')

def read_tweets_frm_jsonl_file(infilename):
    """
    Reads tweets from a compressed JSONL file and prints each tweet.

    Argument(s):
    - infilename: String representing the input file path (.json.gz).

    Output:
    Prints each tweet to the console.
    """
    try:
        with gzip.open(infilename, 'rb') as infile:
            counter = 1
            for tweet in infile:
                tweet = json.loads(tweet.decode())
                print(f'reading tweets: {counter}')
                counter += 1
    except:
        genericErrorInfo()

def dumpJsonToFile(outfilename, dictToWrite, indentFlag=False, extraParams=None):
    """
    Dumps a dictionary to a JSON file with optional formatting.

    Argument(s):
    - outfilename: String representing the file path where JSON data will be saved.
    - dictToWrite: Dictionary to write into the file.
    - indentFlag: Boolean indicating if the JSON should be pretty-printed with indentation.
    - extraParams: Optional dictionary with additional parameters like verbosity.

    Output:
    Creates a JSON file with the specified dictionary content.
    """
    if extraParams is None:
        extraParams = {}

    extraParams.setdefault('verbose', True)

    try:
        with open(outfilename, 'w') as outfile:
            if indentFlag:
                json.dump(dictToWrite, outfile, ensure_ascii=False, indent=4)
            else:
                json.dump(dictToWrite, outfile, ensure_ascii=False)

        if extraParams['verbose']:
            print('\tdumpJsonToFile(), wrote:', outfilename)
    except:
        if extraParams['verbose']:
            print('\terror: outfilename:', outfilename)
        genericErrorInfo()
